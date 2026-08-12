/**
 * @NApiVersion 2.1
 * @NScriptType Suitelet
 * @NModuleScope SameAccount
 *
 * KE monthly Order Fulfillment charge review and invoice creation.
 *
 * Data rules:
 * - Purchase-side charges are selected by Item Receipt date and sourced from
 *   the related Purchase Order.
 * - Sales-side charges are selected by Item Fulfillment date and sourced from
 *   the related Sales Order.
 * - Storage is quantity on hand as of period end, by customer-owned location.
 * - Location.custrecord_order_fulfillment_entity supplies the invoice customer.
 * - One open invoice is created per customer/subsidiary for the month, built
 *   from one line per individual charge (not summed by code) so each source
 *   transaction's contribution stays visible on the invoice.
 *
 * Before deployment, create the transaction body field configured as
 * SOURCE_INVOICE_FIELD. It must be List/Record -> Transaction, apply to Sale
 * and Purchase transactions, and store value. It prevents a PO/SO from being
 * billed again in a later month after partial receipts/fulfillments.
 *
 * Page flow: pick a customer + period at top (a status banner shows whether
 * that customer/period was already invoiced), review the resulting charges
 * below — each editable and linked back to its source PO/SO — then submit to
 * confirm and create the invoice.
 */
define(['N/ui/serverWidget', 'N/search', 'N/record', 'N/format', 'N/log', 'N/url'],
    (serverWidget, search, record, format, log, url) => {

    const CONFIG = Object.freeze({
        LOCATION_CUSTOMER_FIELD: 'custrecord_order_fulfillment_entity',
        VENDOR_OF_FIELD: 'custentity_order_fulfillment_entity',

        // Create this field or replace with the equivalent existing field ID.
        SOURCE_INVOICE_FIELD: 'custbody_of_invoice_created',

        BODY: {
            WAREHOUSE_ARRIVAL: 'custbody_warehouse_arrival_fee',
            DUTY: 'custbody_duty',
            SHIPPING: 'custbody_shipping_charges',
            FISCAL_REP_FEE: 'custbody_fiscal_representation_fee',
            FISCAL_REP: 'custbody_fiscal_representative',
            CUSTOMER_SERVICE: 'custbody_customer_service',
            PICK_PACK: 'custbody_pick_and_pack',
            HANDLING: 'custbody_handling',
            LAST_MILE: 'custbody_last_mile_delivery',
            TOTAL: 'custbody_total',
            TOTAL_VAT: 'custbody_total_vat_value',
            TOTAL_SALES: 'custbody_total_sales_value'
        },

        ITEM_RATE: {
            INBOUND: 'custitem_inbound',
            FIRST: 'custitem_1_item',
            ADD_1_5: 'custitem_additional_15_units',
            ADD_6_10: 'custitem_additional_610_units',
            ADD_11_PLUS: 'custitem_additional_11_units',
            HANDLING_PER_ORDER: 'custitem_handling_fee_per_order',
            STORAGE: 'custitem_monthly_storage_fee',
            IMPORT_VALUE: 'custitem_import_value'
        },

        INVOICE_ITEMS: {
            OF1: 42014,
            OF2: 42015,
            OF3: 42016,
            OF4: 42017, // Deliberately unused for now.
            OF5: 42018,
            OF6: 42019,
            OF7: 42020,
            OF8: 42021
        },

        DESCRIPTIONS: {
            OF1: 'Customer Service Monthly Fee',
            OF2: 'Fiscal Representation Fee',
            OF3: 'Last Mile Delivery',
            OF4: 'Container Fee',
            OF5: 'Order Fulfillment Fee',
            OF6: 'Storage Fee',
            OF7: 'Warehouse Arrival Fee',
            OF8: 'Import Clearance'
        },

        INVOICE_FORM_ID: null,
        FORCE_APPROVED: true,
        MAX_SOURCE_RESULTS: 10000
    });

    const PAGE = Object.freeze({
        START: 'custpage_start_date',
        END: 'custpage_end_date',
        CUSTOMER: 'custpage_customer',
        CONFIRM: 'custpage_confirm_create',
        CHARGES: 'custpage_charges_list',
        INCLUDE: 'custpage_include',
        GROUP_KEY: 'custpage_group_key',
        SOURCE_TYPE: 'custpage_source_type',
        SOURCE_ID: 'custpage_source_id'
    });

    function number(value) {
        const parsed = Number(value || 0);
        return Number.isFinite(parsed) ? parsed : 0;
    }

    function money(value) {
        return Math.round((number(value) + Number.EPSILON) * 100) / 100;
    }

    function priorMonth() {
        const now = new Date();
        return {
            startDate: new Date(now.getFullYear(), now.getMonth() - 1, 1),
            endDate: new Date(now.getFullYear(), now.getMonth(), 0)
        };
    }

    function parseDate(value, fallback) {
        return value ? format.parse({ value, type: format.Type.DATE }) : fallback;
    }

    function dateText(value) {
        return format.format({ value, type: format.Type.DATE });
    }

    function monthKey(endDate) {
        return `${endDate.getFullYear()}${String(endDate.getMonth() + 1).padStart(2, '0')}`;
    }

    function loadAll(searchObj) {
        const rows = [];
        const paged = searchObj.runPaged({ pageSize: 1000 });
        paged.pageRanges.forEach(range => {
            if (rows.length >= CONFIG.MAX_SOURCE_RESULTS) return;
            paged.fetch({ index: range.index }).data.forEach(row => {
                if (rows.length < CONFIG.MAX_SOURCE_RESULTS) rows.push(row);
            });
        });
        return rows;
    }

    function lookupLocation(locationId, cache) {
        if (!locationId) return null;
        if (cache[locationId] !== undefined) return cache[locationId];
        const values = search.lookupFields({
            type: search.Type.LOCATION,
            id: locationId,
            columns: ['name', 'subsidiary', CONFIG.LOCATION_CUSTOMER_FIELD]
        });
        const customer = values[CONFIG.LOCATION_CUSTOMER_FIELD];
        const subsidiary = values.subsidiary;
        cache[locationId] = {
            locationId: String(locationId),
            locationText: values.name || String(locationId),
            customerId: customer && customer[0] ? String(customer[0].value) : '',
            customerText: customer && customer[0] ? customer[0].text : '',
            subsidiaryId: subsidiary && subsidiary[0] ? String(subsidiary[0].value) : ''
        };
        return cache[locationId];
    }

    function lookupCustomer(customerId, cache) {
        if (!customerId) return '';
        if (!cache[customerId]) {
            const values = search.lookupFields({ type: search.Type.CUSTOMER, id: customerId, columns: ['entityid', 'companyname'] });
            cache[customerId] = values.companyname || values.entityid || String(customerId);
        }
        return cache[customerId];
    }

    function charge(options) {
        const amount = money(options.amount);
        if (!amount) return null;
        return {
            customerId: String(options.customerId || ''),
            customerText: options.customerText || '',
            subsidiaryId: String(options.subsidiaryId || ''),
            code: options.code,
            description: CONFIG.DESCRIPTIONS[options.code],
            amount,
            sourceType: options.sourceType || '',
            sourceId: String(options.sourceId || ''),
            sourceText: options.sourceText || '',
            locationId: String(options.locationId || ''),
            locationText: options.locationText || '',
            memo: options.memo || ''
        };
    }

    function pushCharge(charges, options) {
        const row = charge(options);
        if (row && row.customerId) charges.push(row);
    }

    function chunks(values, size) {
        const output = [];
        for (let index = 0; index < values.length; index += size) {
            output.push(values.slice(index, index + size));
        }
        return output;
    }

    function isInvalidColumnError(error) {
        return !!error && (error.name === 'SSS_INVALID_SRCH_COL' || error.name === 'INVALID_SRCH_COL');
    }

    /** Pulls the offending field id out of the SSS_INVALID_SRCH_COL message text. */
    function extractInvalidColumnName(error) {
        const message = (error && error.message) || '';
        const match = message.match(/:\s*([^\s]+)\s*$/);
        return match ? match[1].replace(/\.+$/, '') : null;
    }

    /**
     * Load transaction headers in batched searches. A record.load on a standard
     * transaction costs 10 governance units; loading hundreds individually can
     * exhaust a Suitelet's 1,000-unit allowance before the page renders.
     *
     * Body columns (including SOURCE_INVOICE_FIELD) are requested defensively:
     * any of them may be invalid for this record type — field not created yet,
     * or its "Applies To"/sourcing config doesn't cover this transaction type —
     * which makes NetSuite reject the whole search with SSS_INVALID_SRCH_COL.
     * Rather than let one bad field take down the Suitelet, we identify which
     * column NetSuite rejected, drop only that one, and retry — looping until
     * the search succeeds (or, if we can't isolate the culprit, drop every
     * optional column at once so this can never crash the page outright).
     * Every dropped column is recorded in `diagnostics` so the UI can warn the
     * admin (skipped fields read as 0/blank) instead of the page just crashing.
     */
    function loadTransactionHeaders(type, ids, cache, diagnostics) {
        const uniqueIds = [...new Set(ids.map(String).filter(Boolean))]
            .filter(id => !cache[`${type}:${id}`]);
        if (!uniqueIds.length) return;

        if (diagnostics) diagnostics.invalidColumns = diagnostics.invalidColumns || {};
        const knownBad = (diagnostics && diagnostics.invalidColumns[type]) || new Set();
        if (diagnostics) diagnostics.invalidColumns[type] = knownBad;

        const optionalColumns = [CONFIG.SOURCE_INVOICE_FIELD].concat(Object.keys(CONFIG.BODY).map(keyName => CONFIG.BODY[keyName]));
        const fixedColumns = ['internalid', 'tranid', 'entity', 'subsidiary'];
        let requestColumns = fixedColumns.concat(optionalColumns.filter(col => !knownBad.has(col)));

        chunks(uniqueIds, 500).forEach(batch => {
            let rows;
            for (;;) {
                try {
                    rows = loadAll(search.create({
                        type,
                        filters: [
                            ['mainline', search.Operator.IS, 'T'], 'AND',
                            ['internalid', search.Operator.ANYOF, batch]
                        ],
                        columns: requestColumns
                    }));
                    break;
                } catch (error) {
                    const looksLikeInvalidColumn = isInvalidColumnError(error)
                        || /invalid column|not in proper syntax/i.test((error && error.message) || '');
                    if (!looksLikeInvalidColumn) throw error;

                    const optionalInRequest = requestColumns.filter(col => !fixedColumns.includes(col));
                    if (!optionalInRequest.length) throw error; // Nothing optional left to drop — a fixed column is broken.

                    const badColumn = extractInvalidColumnName(error);
                    const toDrop = badColumn && requestColumns.includes(badColumn) ? [badColumn] : optionalInRequest;
                    toDrop.forEach(col => knownBad.add(col));
                    requestColumns = requestColumns.filter(col => !toDrop.includes(col));
                    log.audit({
                        title: 'Invalid search column(s) skipped',
                        details: `${toDrop.length === 1 ? `Column "${toDrop[0]}"` : `Columns [${toDrop.join(', ')}] (could not isolate which one NetSuite rejected, so all optional columns were dropped)`} invalid on a ${type} search. Verify the field(s) exist, store a value, and their Applies To/sourcing config covers this record type. Skipping for this run — dependent amounts will read as 0. Original error: ${error.message}`
                    });
                }
            }

            rows.forEach(row => {
                const id = String(row.id);
                cache[`${type}:${id}`] = {
                    id,
                    tranid: row.getValue({ name: 'tranid' }) || id,
                    entity: String(row.getValue({ name: 'entity' }) || ''),
                    entityText: row.getText({ name: 'entity' }) || '',
                    subsidiary: String(row.getValue({ name: 'subsidiary' }) || ''),
                    alreadyInvoiced: knownBad.has(CONFIG.SOURCE_INVOICE_FIELD) ? '' : String(row.getValue({ name: CONFIG.SOURCE_INVOICE_FIELD }) || ''),
                    values: Object.keys(CONFIG.BODY).reduce((out, keyName) => {
                        out[keyName] = knownBad.has(CONFIG.BODY[keyName]) ? 0 : row.getValue({ name: CONFIG.BODY[keyName] });
                        return out;
                    }, {})
                };
            });
        });
    }

    function loadVendorEligibility(vendorIds, cache) {
        const uniqueIds = [...new Set(vendorIds.map(String).filter(Boolean))]
            .filter(id => cache[id] === undefined);
        chunks(uniqueIds, 500).forEach(batch => {
            const rows = loadAll(search.create({
                type: search.Type.VENDOR,
                filters: [['internalid', search.Operator.ANYOF, batch]],
                columns: ['internalid', CONFIG.VENDOR_OF_FIELD]
            }));
            batch.forEach(id => { cache[id] = false; });
            rows.forEach(row => {
                const value = row.getValue({ name: CONFIG.VENDOR_OF_FIELD });
                cache[String(row.id)] = !(value === false || value === 'F' || value === '' || value === null);
            });
        });
    }

    /** Add PO-level charges once when its first eligible receipt occurs in the period. */
    function collectInbound(period, filters, caches, charges, sourceRecords) {
        const receiptRows = loadAll(search.create({
            type: search.Type.ITEM_RECEIPT,
            filters: [
                ['mainline', search.Operator.IS, 'F'], 'AND',
                ['taxline', search.Operator.IS, 'F'], 'AND',
                ['shipping', search.Operator.IS, 'F'], 'AND',
                ['trandate', search.Operator.ONORAFTER, dateText(period.startDate)], 'AND',
                ['trandate', search.Operator.ONORBEFORE, dateText(period.endDate)], 'AND',
                ['item', search.Operator.NONEOF, '@NONE@'], 'AND',
                ['location', search.Operator.NONEOF, '@NONE@'], 'AND',
                // Item Receipts may also be created from Transfer Orders.
                // Only receipts created from Purchase Orders are billable here.
                ['createdfrom.type', search.Operator.ANYOF, 'PurchOrd']
            ],
            columns: ['internalid', 'tranid', 'createdfrom', 'location']
        }));

        const poContexts = {};
        const poCustomers = {};
        receiptRows.forEach(row => {
            const poId = String(row.getValue({ name: 'createdfrom' }) || '');
            const locationId = String(row.getValue({ name: 'location' }) || '');
            if (!poId || !locationId) return;
            const loc = lookupLocation(locationId, caches.locations);
            if (!loc || !loc.customerId || (filters.customerId && loc.customerId !== filters.customerId)) return;
            const key = `${poId}|${loc.customerId}|${loc.subsidiaryId}`;
            if (!poContexts[key]) poContexts[key] = { poId, loc };
            if (!poCustomers[poId]) poCustomers[poId] = new Set();
            poCustomers[poId].add(loc.customerId);
        });

        Object.keys(poCustomers).forEach(poId => {
            if (poCustomers[poId].size > 1) {
                throw new Error(`Purchase Order ${poId} received into locations belonging to multiple OF customers. Split or correct the receipt before billing.`);
            }
        });

        const poIds = Object.values(poContexts).map(context => context.poId);
        loadTransactionHeaders(search.Type.PURCHASE_ORDER, poIds, caches.transactions, caches.diagnostics);
        const purchaseOrders = poIds.map(id => caches.transactions[`${search.Type.PURCHASE_ORDER}:${id}`]).filter(Boolean);
        loadVendorEligibility(purchaseOrders.map(po => po.entity), caches.vendors);

        Object.keys(poContexts).forEach(key => {
            const context = poContexts[key];
            const po = caches.transactions[`${search.Type.PURCHASE_ORDER}:${context.poId}`];
            if (!po || po.alreadyInvoiced) return;

            // Vendor field is treated as an eligibility flag. If it is a select,
            // any populated value also qualifies the vendor.
            if (!po.entity || !caches.vendors[po.entity]) return;

            const base = {
                customerId: context.loc.customerId,
                customerText: context.loc.customerText,
                subsidiaryId: context.loc.subsidiaryId || po.subsidiary,
                sourceType: record.Type.PURCHASE_ORDER,
                sourceId: po.id,
                sourceText: po.tranid,
                locationId: context.loc.locationId,
                locationText: context.loc.locationText
            };
            pushCharge(charges, { ...base, code: 'OF2', amount: po.values.FISCAL_REP_FEE });
            pushCharge(charges, { ...base, code: 'OF7', amount: po.values.WAREHOUSE_ARRIVAL });
            pushCharge(charges, {
                ...base,
                code: 'OF8',
                amount: number(po.values.SHIPPING) + number(po.values.DUTY),
                memo: `Shipping ${money(po.values.SHIPPING).toFixed(2)} + duty ${money(po.values.DUTY).toFixed(2)}`
            });
            sourceRecords[key] = { type: record.Type.PURCHASE_ORDER, id: po.id };
        });
    }

    /** Add SO-level charges once when at least one fulfillment occurs in period. */
    function collectOutbound(period, filters, caches, charges, sourceRecords) {
        const fulfillmentRows = loadAll(search.create({
            type: search.Type.ITEM_FULFILLMENT,
            filters: [
                ['mainline', search.Operator.IS, 'T'], 'AND',
                ['trandate', search.Operator.ONORAFTER, dateText(period.startDate)], 'AND',
                ['trandate', search.Operator.ONORBEFORE, dateText(period.endDate)], 'AND',
                ['createdfrom', search.Operator.NONEOF, '@NONE@'], 'AND',
                // Item Fulfillments may also be created from Transfer Orders.
                // Loading those IDs as Sales Orders causes INVALID_TRANS_TYP.
                ['createdfrom.type', search.Operator.ANYOF, 'SalesOrd']
            ],
            columns: ['internalid', 'tranid', 'createdfrom']
        }));

        const salesOrders = new Set(fulfillmentRows.map(row => String(row.getValue({ name: 'createdfrom' }) || '')).filter(Boolean));
        loadTransactionHeaders(search.Type.SALES_ORDER, [...salesOrders], caches.transactions, caches.diagnostics);
        salesOrders.forEach(soId => {
            const so = caches.transactions[`${search.Type.SALES_ORDER}:${soId}`];
            if (!so || so.alreadyInvoiced || (filters.customerId && so.entity !== filters.customerId)) return;
            const base = {
                customerId: so.entity,
                customerText: so.entityText,
                subsidiaryId: so.subsidiary,
                sourceType: record.Type.SALES_ORDER,
                sourceId: so.id,
                sourceText: so.tranid
            };
            pushCharge(charges, { ...base, code: 'OF1', amount: so.values.CUSTOMER_SERVICE });
            pushCharge(charges, { ...base, code: 'OF3', amount: so.values.LAST_MILE });
            // Per confirmed rule, handling already includes customer service and
            // pick-and-pack, while OF1 remains a separate charge for now.
            pushCharge(charges, { ...base, code: 'OF5', amount: so.values.HANDLING });
            sourceRecords[`salesorder|${so.id}`] = { type: record.Type.SALES_ORDER, id: so.id };
        });
    }

    /** Calculate historical month-end quantity on hand from posting inventory activity. */
    function collectStorage(period, filters, caches, charges) {
        const locationFilters = [[CONFIG.LOCATION_CUSTOMER_FIELD, search.Operator.NONEOF, '@NONE@'], 'AND', ['isinactive', search.Operator.IS, 'F']];
        if (filters.customerId) locationFilters.push('AND', [CONFIG.LOCATION_CUSTOMER_FIELD, search.Operator.ANYOF, filters.customerId]);
        const locationRows = loadAll(search.create({
            type: search.Type.LOCATION,
            filters: locationFilters,
            columns: ['internalid', 'name', 'subsidiary', CONFIG.LOCATION_CUSTOMER_FIELD]
        }));
        const locations = locationRows.map(row => lookupLocation(String(row.id), caches.locations)).filter(loc => loc && loc.customerId);
        if (!locations.length) return;

        const inventoryRows = loadAll(search.create({
            type: search.Type.TRANSACTION,
            filters: [
                ['posting', search.Operator.IS, 'T'], 'AND',
                ['trandate', search.Operator.ONORBEFORE, dateText(period.endDate)], 'AND',
                ['accounttype', search.Operator.ANYOF, 'InvtAsset'], 'AND',
                ['location', search.Operator.ANYOF, locations.map(loc => loc.locationId)], 'AND',
                ['item', search.Operator.NONEOF, '@NONE@']
            ],
            columns: [
                search.createColumn({ name: 'location', summary: search.Summary.GROUP }),
                search.createColumn({ name: 'item', summary: search.Summary.GROUP }),
                search.createColumn({ name: 'quantity', summary: search.Summary.SUM }),
                search.createColumn({ name: CONFIG.ITEM_RATE.STORAGE, join: 'item', summary: search.Summary.MAX })
            ]
        }));

        inventoryRows.forEach(row => {
            const locationId = String(row.getValue({ name: 'location', summary: search.Summary.GROUP }) || '');
            const itemId = String(row.getValue({ name: 'item', summary: search.Summary.GROUP }) || '');
            const quantity = number(row.getValue({ name: 'quantity', summary: search.Summary.SUM }));
            const rate = number(row.getValue({ name: CONFIG.ITEM_RATE.STORAGE, join: 'item', summary: search.Summary.MAX }));
            const loc = lookupLocation(locationId, caches.locations);
            if (!loc || quantity <= 0 || rate <= 0) return;
            pushCharge(charges, {
                customerId: loc.customerId,
                customerText: loc.customerText,
                subsidiaryId: loc.subsidiaryId,
                code: 'OF6',
                amount: quantity * rate,
                sourceType: 'inventory',
                sourceId: itemId,
                sourceText: `Item ${itemId}`,
                locationId,
                locationText: loc.locationText,
                memo: `${quantity} units × ${rate.toFixed(2)}`
            });
        });
    }

    function groupKey(row) {
        return `${row.customerId}|${row.subsidiaryId || ''}`;
    }

    /** Invoices already created by this script for the period, keyed by their KE-OF-... external id. */
    function existingInvoiceBatches(endDate) {
        const prefix = `KE-OF-${monthKey(endDate)}-`;
        const batches = new Map();
        loadAll(search.create({
            type: search.Type.INVOICE,
            filters: [['mainline', search.Operator.IS, 'T'], 'AND', ['externalidstring', search.Operator.STARTSWITH, prefix]],
            columns: ['externalid', 'internalid', 'tranid']
        })).forEach(row => {
            const externalId = String(row.getValue({ name: 'externalid' }) || '');
            if (externalId) batches.set(externalId, { id: String(row.id), tranid: row.getValue({ name: 'tranid' }) || String(row.id) });
        });
        return batches;
    }

    function collectModel(period, customerId) {
        const charges = [];
        const sourceRecords = {};
        const caches = { locations: {}, customers: {}, transactions: {}, vendors: {}, diagnostics: { invalidColumns: {} } };
        const filters = { customerId: String(customerId || '') };
        collectInbound(period, filters, caches, charges, sourceRecords);
        collectOutbound(period, filters, caches, charges, sourceRecords);
        collectStorage(period, filters, caches, charges);

        const invoicedBatches = existingInvoiceBatches(period.endDate);
        const groups = {};
        charges.forEach(row => {
            const key = groupKey(row);
            const externalId = `KE-OF-${monthKey(period.endDate)}-${row.customerId}-${row.subsidiaryId || 'NA'}`;
            if (invoicedBatches.has(externalId)) return;
            if (!groups[key]) {
                groups[key] = {
                    key,
                    externalId,
                    customerId: row.customerId,
                    customerText: row.customerText || lookupCustomer(row.customerId, caches.customers),
                    subsidiaryId: row.subsidiaryId,
                    charges: [],
                    total: 0
                };
            }
            groups[key].charges.push(row);
            groups[key].total = money(groups[key].total + row.amount);
        });
        return { groups, sourceRecords, diagnostics: caches.diagnostics, invoicedBatches };
    }

    function addValue(sublist, id, line, value) {
        if (value !== '' && value !== null && value !== undefined) {
            sublist.setSublistValue({ id, line, value: String(value) });
        }
    }

    /** Only PO/SO-sourced charges have a real transaction to drill into. */
    function sourceUrl(row) {
        if (row.sourceType !== record.Type.PURCHASE_ORDER && row.sourceType !== record.Type.SALES_ORDER) return '';
        if (!row.sourceId) return '';
        try {
            return url.resolveRecord({ recordType: row.sourceType, recordId: row.sourceId, isEditMode: false });
        } catch (error) {
            log.debug({ title: 'Could not resolve source transaction URL', details: error.message });
            return '';
        }
    }

    function statusHtml(customerId, invoicedForCustomer, groups, message) {
        const total = groups.reduce((sum, group) => sum + group.total, 0);
        const chargeCount = groups.reduce((count, group) => count + group.charges.length, 0);

        let statusLine;
        if (!customerId) {
            statusLine = '<span style="color:#5a6472">Select a customer above to review this period\'s charges.</span>';
        } else if (invoicedForCustomer.length) {
            const refs = invoicedForCustomer.map(entry => `Invoice #${entry.tranid}`).join(', ');
            statusLine = `<span style="color:#176b2c"><b>Already invoiced</b> for this period — ${refs}.</span>`;
        } else if (!groups.length) {
            statusLine = '<span style="color:#5a6472">Not yet invoiced — no billable charges found for this customer/period.</span>';
        } else {
            statusLine = `<span style="color:#8a5a00"><b>Not yet invoiced</b> — ${chargeCount} charge(s) totaling ${money(total).toFixed(2)} ready for review below.</span>`;
        }

        return `<div style="padding:12px;background:#f4f7fa;border:1px solid #d5dce5;margin:8px 0;">
            ${statusLine}
            ${message ? `<div style="margin-top:8px;color:#176b2c"><b>${message}</b></div>` : ''}
        </div>`;
    }

    function buildForm(period, customerId, model, invoicedForCustomer, message) {
        const form = serverWidget.createForm({ title: 'Monthly Order Fulfillment Charge Review' });
        const start = form.addField({ id: PAGE.START, type: serverWidget.FieldType.DATE, label: 'Period Start' });
        start.isMandatory = true;
        start.defaultValue = dateText(period.startDate);
        const end = form.addField({ id: PAGE.END, type: serverWidget.FieldType.DATE, label: 'Period End' });
        end.isMandatory = true;
        end.defaultValue = dateText(period.endDate);
        const customer = form.addField({ id: PAGE.CUSTOMER, type: serverWidget.FieldType.SELECT, label: 'Customer', source: 'customer' });
        customer.isMandatory = true;
        customer.defaultValue = customerId || '';

        const groups = Object.values(model.groups).sort((a, b) => a.customerText.localeCompare(b.customerText));
        const html = form.addField({ id: 'custpage_status_html', type: serverWidget.FieldType.INLINEHTML, label: 'Status' });
        html.defaultValue = statusHtml(customerId, invoicedForCustomer, groups, message);

        const alreadyInvoiced = customerId && invoicedForCustomer.length;
        if (customerId && !alreadyInvoiced && groups.length) {
            const confirm = form.addField({ id: PAGE.CONFIRM, type: serverWidget.FieldType.CHECKBOX, label: 'Confirm: create the invoice below for this customer/period' });
            confirm.defaultValue = 'F';
        }

        // INLINEEDITOR so amount/description are directly editable per charge —
        // a search-sourced value that came back 0 (missing/misconfigured search
        // column) can be corrected by hand instead of blocking invoice creation.
        // addMarkAllButtons() is not supported on INLINEEDITOR, so rows default
        // to included and staff uncheck specific ones to exclude them instead.
        const charges = form.addSublist({ id: PAGE.CHARGES, type: serverWidget.SublistType.INLINEEDITOR, label: 'Charges — Edit or Exclude, Then Confirm Above to Invoice' });
        charges.addField({ id: PAGE.INCLUDE, type: serverWidget.FieldType.CHECKBOX, label: 'Include' });
        charges.addField({ id: PAGE.GROUP_KEY, type: serverWidget.FieldType.TEXT, label: 'Group Key' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.HIDDEN });
        charges.addField({ id: PAGE.SOURCE_TYPE, type: serverWidget.FieldType.TEXT, label: 'Source Record Type' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.HIDDEN });
        charges.addField({ id: PAGE.SOURCE_ID, type: serverWidget.FieldType.TEXT, label: 'Source Record Id' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.HIDDEN });
        charges.addField({ id: 'custpage_charge_code', type: serverWidget.FieldType.TEXT, label: 'Code' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.DISABLED });
        charges.addField({ id: 'custpage_charge_description', type: serverWidget.FieldType.TEXT, label: 'Description' });
        charges.addField({ id: 'custpage_charge_amount', type: serverWidget.FieldType.CURRENCY, label: 'Amount' });
        charges.addField({ id: 'custpage_charge_source', type: serverWidget.FieldType.TEXT, label: 'Source Transaction' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.DISABLED });
        charges.addField({ id: 'custpage_charge_view', type: serverWidget.FieldType.URL, label: 'View Source' });
        charges.addField({ id: 'custpage_charge_location', type: serverWidget.FieldType.TEXT, label: 'Location' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.DISABLED });
        charges.addField({ id: 'custpage_charge_calc', type: serverWidget.FieldType.TEXT, label: 'Calculation' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.DISABLED });

        let line = 0;
        groups.forEach(group => group.charges.forEach(row => {
            addValue(charges, PAGE.INCLUDE, line, 'T');
            addValue(charges, PAGE.GROUP_KEY, line, group.key);
            addValue(charges, PAGE.SOURCE_TYPE, line, row.sourceType);
            addValue(charges, PAGE.SOURCE_ID, line, row.sourceId);
            addValue(charges, 'custpage_charge_code', line, row.code);
            addValue(charges, 'custpage_charge_description', line, `${group.customerText}: ${row.description}`);
            addValue(charges, 'custpage_charge_amount', line, row.amount.toFixed(2));
            addValue(charges, 'custpage_charge_source', line, row.sourceText);
            addValue(charges, 'custpage_charge_view', line, sourceUrl(row));
            addValue(charges, 'custpage_charge_location', line, row.locationText);
            addValue(charges, 'custpage_charge_calc', line, row.memo);
            line += 1;
        }));

        if (customerId && !alreadyInvoiced && groups.length) {
            form.addSubmitButton({ label: 'Create Invoice' });
        } else {
            form.addSubmitButton({ label: 'Apply Filters' });
        }
        return form;
    }

    /**
     * Reads the (possibly staff-edited) charge grid back out of the request,
     * grouped by group key. Each row keeps its own amount/description rather
     * than being summed by code, so the resulting invoice mirrors what was on
     * screen — including manual corrections and excluded rows — line for line.
     */
    function readChargeRows(request) {
        const rowsByGroup = {};
        const count = request.getLineCount({ group: PAGE.CHARGES });
        for (let line = 0; line < count; line += 1) {
            if (request.getSublistValue({ group: PAGE.CHARGES, name: PAGE.INCLUDE, line }) !== 'T') continue;
            const key = String(request.getSublistValue({ group: PAGE.CHARGES, name: PAGE.GROUP_KEY, line }));
            const amount = money(request.getSublistValue({ group: PAGE.CHARGES, name: 'custpage_charge_amount', line }));
            if (!amount) continue;
            (rowsByGroup[key] = rowsByGroup[key] || []).push({
                code: request.getSublistValue({ group: PAGE.CHARGES, name: 'custpage_charge_code', line }),
                description: request.getSublistValue({ group: PAGE.CHARGES, name: 'custpage_charge_description', line }),
                amount,
                sourceType: request.getSublistValue({ group: PAGE.CHARGES, name: PAGE.SOURCE_TYPE, line }),
                sourceId: request.getSublistValue({ group: PAGE.CHARGES, name: PAGE.SOURCE_ID, line })
            });
        }
        return rowsByGroup;
    }

    /** One invoice line per charge row — matches the source data 1:1 instead of summing by code. */
    function createInvoiceFromRows(group, period, rows) {
        const invoice = record.create({ type: record.Type.INVOICE, isDynamic: false });
        if (CONFIG.INVOICE_FORM_ID) invoice.setValue({ fieldId: 'customform', value: CONFIG.INVOICE_FORM_ID });
        if (group.subsidiaryId) invoice.setValue({ fieldId: 'subsidiary', value: Number(group.subsidiaryId) });
        invoice.setValue({ fieldId: 'entity', value: Number(group.customerId) });
        invoice.setValue({ fieldId: 'trandate', value: period.endDate });
        invoice.setValue({ fieldId: 'externalid', value: group.externalId });
        invoice.setValue({ fieldId: 'memo', value: `Order Fulfillment charges: ${dateText(period.startDate)} - ${dateText(period.endDate)}` });
        if (CONFIG.FORCE_APPROVED) {
            try { invoice.setValue({ fieldId: 'approvalstatus', value: 2 }); } catch (error) {
                log.debug({ title: 'Invoice approval status not available', details: error.message });
            }
        }

        rows.forEach((row, line) => {
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'item', line, value: CONFIG.INVOICE_ITEMS[row.code] });
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'quantity', line, value: 1 });
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'rate', line, value: row.amount });
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'description', line, value: String(row.description || '').slice(0, 999) });
        });
        return String(invoice.save({ enableSourcing: true, ignoreMandatoryFields: false }));
    }

    function markSourceTransactions(rows, invoiceId) {
        const unique = {};
        rows.filter(row => row.sourceType === record.Type.PURCHASE_ORDER || row.sourceType === record.Type.SALES_ORDER)
            .forEach(row => { unique[`${row.sourceType}|${row.sourceId}`] = row; });
        Object.values(unique).forEach(row => {
            record.submitFields({
                type: row.sourceType,
                id: Number(row.sourceId),
                values: { [CONFIG.SOURCE_INVOICE_FIELD]: Number(invoiceId) },
                options: { enableSourcing: false, ignoreMandatoryFields: false }
            });
        });
    }

    function onRequest(context) {
        const defaults = priorMonth();
        const params = context.request.parameters;
        const period = {
            startDate: parseDate(params[PAGE.START], defaults.startDate),
            endDate: parseDate(params[PAGE.END], defaults.endDate)
        };
        const customerId = String(params[PAGE.CUSTOMER] || '');
        // Collecting is scoped to one customer at a time — no customer, no search cost.
        let model = customerId
            ? collectModel(period, customerId)
            : { groups: {}, sourceRecords: {}, diagnostics: { invalidColumns: {} }, invoicedBatches: new Map() };
        let message = '';

        if (context.request.method === 'POST' && customerId && params[PAGE.CONFIRM] === 'T') {
            const rowsByGroup = readChargeRows(context.request);
            const created = [];
            Object.keys(rowsByGroup).forEach(key => {
                const group = model.groups[key];
                const rows = rowsByGroup[key];
                if (!group || !rows.length) return;
                const invoiceId = createInvoiceFromRows(group, period, rows);
                markSourceTransactions(rows, invoiceId);
                created.push({ invoiceId, amount: rows.reduce((sum, row) => sum + row.amount, 0) });
            });
            if (created.length) {
                message = `Created ${created.length} invoice(s), total ${money(created.reduce((sum, row) => sum + row.amount, 0)).toFixed(2)}.`;
                model = collectModel(period, customerId);
            } else {
                message = 'Nothing was included to invoice.';
            }
        }

        const invalidColumnNotes = Object.keys(model.diagnostics && model.diagnostics.invalidColumns || {})
            .map(type => ({ type, columns: [...model.diagnostics.invalidColumns[type]] }))
            .filter(entry => entry.columns.length)
            .map(entry => `${entry.type}: ${entry.columns.join(', ')}`);
        if (invalidColumnNotes.length) {
            message = `Warning: these fields are invalid search columns on the noted transaction type right now — likely missing, or Applies To/sourcing config doesn't cover that type — so they were skipped this run (amounts sourced from them read as 0 below; edit the Amount column directly if you need to correct them before creating the invoice; if the skipped field is "${CONFIG.SOURCE_INVOICE_FIELD}", duplicate-invoice protection is also OFF). Fix the field(s) in NetSuite, then re-run. ${invalidColumnNotes.join(' | ')} ${message}`;
        }

        const invoicedForCustomer = customerId
            ? [...model.invoicedBatches.entries()]
                .filter(([key]) => key.startsWith(`KE-OF-${monthKey(period.endDate)}-${customerId}-`))
                .map(([, entry]) => entry)
            : [];

        context.response.writePage(buildForm(period, customerId, model, invoicedForCustomer, message));
    }

    return { onRequest };
});
