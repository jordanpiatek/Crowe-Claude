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
 * - One open invoice is created per selected customer/subsidiary for the month.
 *
 * Before deployment, create the transaction body field configured as
 * SOURCE_INVOICE_FIELD. It must be List/Record -> Transaction, apply to Sale
 * and Purchase transactions, and store value. It prevents a PO/SO from being
 * billed again in a later month after partial receipts/fulfillments.
 */
define(['N/ui/serverWidget', 'N/search', 'N/record', 'N/format', 'N/log'],
    (serverWidget, search, record, format, log) => {

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
        SUMMARY: 'custpage_summary_list',
        DETAILS: 'custpage_detail_list',
        SELECT: 'custpage_select',
        GROUP_KEY: 'custpage_group_key'
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
     * the search succeeds. Every dropped column is recorded in `diagnostics` so
     * the UI can warn the admin (skipped fields read as 0/blank) instead of the
     * page just crashing.
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
                    const badColumn = isInvalidColumnError(error) ? extractInvalidColumnName(error) : null;
                    if (!badColumn || !requestColumns.includes(badColumn)) throw error;
                    knownBad.add(badColumn);
                    requestColumns = requestColumns.filter(col => col !== badColumn);
                    log.audit({
                        title: 'Invalid search column skipped',
                        details: `Column "${badColumn}" is invalid on a ${type} search. Verify the field exists, stores a value, and its Applies To/sourcing config covers this record type. Skipping it for this run — dependent amounts will read as 0. Original error: ${error.message}`
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

    function existingBatchKeys(endDate) {
        const prefix = `KE-OF-${monthKey(endDate)}-`;
        const keys = new Set();
        loadAll(search.create({
            type: search.Type.INVOICE,
            filters: [['mainline', search.Operator.IS, 'T'], 'AND', ['externalidstring', search.Operator.STARTSWITH, prefix]],
            columns: ['externalid']
        })).forEach(row => keys.add(String(row.getValue({ name: 'externalid' }) || '')));
        return keys;
    }

    function collectModel(period, customerId) {
        const charges = [];
        const sourceRecords = {};
        const caches = { locations: {}, customers: {}, transactions: {}, vendors: {}, diagnostics: { invalidColumns: {} } };
        const filters = { customerId: String(customerId || '') };
        collectInbound(period, filters, caches, charges, sourceRecords);
        collectOutbound(period, filters, caches, charges, sourceRecords);
        collectStorage(period, filters, caches, charges);

        const billedKeys = existingBatchKeys(period.endDate);
        const groups = {};
        charges.forEach(row => {
            const key = groupKey(row);
            const externalId = `KE-OF-${monthKey(period.endDate)}-${row.customerId}-${row.subsidiaryId || 'NA'}`;
            if (billedKeys.has(externalId)) return;
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
        return { groups, sourceRecords, diagnostics: caches.diagnostics };
    }

    function addValue(sublist, id, line, value) {
        if (value !== '' && value !== null && value !== undefined) {
            sublist.setSublistValue({ id, line, value: String(value) });
        }
    }

    function buildForm(period, customerId, model, message) {
        const form = serverWidget.createForm({ title: 'Monthly Order Fulfillment Charge Review' });
        const start = form.addField({ id: PAGE.START, type: serverWidget.FieldType.DATE, label: 'Period Start' });
        start.isMandatory = true;
        start.defaultValue = dateText(period.startDate);
        const end = form.addField({ id: PAGE.END, type: serverWidget.FieldType.DATE, label: 'Period End' });
        end.isMandatory = true;
        end.defaultValue = dateText(period.endDate);
        const customer = form.addField({ id: PAGE.CUSTOMER, type: serverWidget.FieldType.SELECT, label: 'Customer', source: 'customer' });
        customer.defaultValue = customerId || '';

        const groups = Object.values(model.groups).sort((a, b) => a.customerText.localeCompare(b.customerText));
        const total = groups.reduce((sum, group) => sum + group.total, 0);
        const summaryHtml = form.addField({ id: 'custpage_summary_html', type: serverWidget.FieldType.INLINEHTML, label: 'Summary' });
        summaryHtml.defaultValue = `<div style="padding:12px;background:#f4f7fa;border:1px solid #d5dce5;margin:8px 0;">
            <b>${groups.length}</b> customer invoice(s) &nbsp; | &nbsp;
            <b>${groups.reduce((count, group) => count + group.charges.length, 0)}</b> charge components &nbsp; | &nbsp;
            <b>${money(total).toFixed(2)}</b> total
            ${message ? `<div style="margin-top:8px;color:#176b2c"><b>${message}</b></div>` : ''}
        </div>`;

        const summary = form.addSublist({ id: PAGE.SUMMARY, type: serverWidget.SublistType.LIST, label: 'Invoices to Create — Select by Customer' });
        summary.addMarkAllButtons();
        summary.addField({ id: PAGE.SELECT, type: serverWidget.FieldType.CHECKBOX, label: 'Create' });
        summary.addField({ id: PAGE.GROUP_KEY, type: serverWidget.FieldType.TEXT, label: 'Group Key' })
            .updateDisplayType({ displayType: serverWidget.FieldDisplayType.HIDDEN });
        summary.addField({ id: 'custpage_customer_name', type: serverWidget.FieldType.TEXT, label: 'Customer' });
        summary.addField({ id: 'custpage_of1', type: serverWidget.FieldType.CURRENCY, label: 'OF1' });
        summary.addField({ id: 'custpage_of2', type: serverWidget.FieldType.CURRENCY, label: 'OF2' });
        summary.addField({ id: 'custpage_of3', type: serverWidget.FieldType.CURRENCY, label: 'OF3' });
        summary.addField({ id: 'custpage_of5', type: serverWidget.FieldType.CURRENCY, label: 'OF5' });
        summary.addField({ id: 'custpage_of6', type: serverWidget.FieldType.CURRENCY, label: 'OF6' });
        summary.addField({ id: 'custpage_of7', type: serverWidget.FieldType.CURRENCY, label: 'OF7' });
        summary.addField({ id: 'custpage_of8', type: serverWidget.FieldType.CURRENCY, label: 'OF8' });
        summary.addField({ id: 'custpage_group_total', type: serverWidget.FieldType.CURRENCY, label: 'Invoice Total' });

        groups.forEach((group, line) => {
            const byCode = group.charges.reduce((out, row) => {
                out[row.code] = money(number(out[row.code]) + row.amount);
                return out;
            }, {});
            addValue(summary, PAGE.GROUP_KEY, line, group.key);
            addValue(summary, 'custpage_customer_name', line, group.customerText);
            ['OF1', 'OF2', 'OF3', 'OF5', 'OF6', 'OF7', 'OF8'].forEach(code => addValue(summary, `custpage_${code.toLowerCase()}`, line, (byCode[code] || 0).toFixed(2)));
            addValue(summary, 'custpage_group_total', line, group.total.toFixed(2));
        });

        const details = form.addSublist({ id: PAGE.DETAILS, type: serverWidget.SublistType.LIST, label: 'Charge Detail' });
        ['Customer', 'Code', 'Description', 'Amount', 'Source', 'Location', 'Calculation'].forEach((label, index) => {
            const ids = ['customer', 'code', 'description', 'amount', 'source', 'location', 'calculation'];
            details.addField({ id: `custpage_detail_${ids[index]}`, type: label === 'Amount' ? serverWidget.FieldType.CURRENCY : serverWidget.FieldType.TEXT, label });
        });
        let detailLine = 0;
        groups.forEach(group => group.charges.forEach(row => {
            addValue(details, 'custpage_detail_customer', detailLine, group.customerText);
            addValue(details, 'custpage_detail_code', detailLine, row.code);
            addValue(details, 'custpage_detail_description', detailLine, row.description);
            addValue(details, 'custpage_detail_amount', detailLine, row.amount.toFixed(2));
            addValue(details, 'custpage_detail_source', detailLine, row.sourceText);
            addValue(details, 'custpage_detail_location', detailLine, row.locationText);
            addValue(details, 'custpage_detail_calculation', detailLine, row.memo);
            detailLine += 1;
        }));

        form.addSubmitButton({ label: 'Apply Filters / Create Selected Open Invoices' });
        return form;
    }

    function selectedGroupKeys(request) {
        const selected = new Set();
        const count = request.getLineCount({ group: PAGE.SUMMARY });
        for (let line = 0; line < count; line += 1) {
            if (request.getSublistValue({ group: PAGE.SUMMARY, name: PAGE.SELECT, line }) === 'T') {
                selected.add(String(request.getSublistValue({ group: PAGE.SUMMARY, name: PAGE.GROUP_KEY, line })));
            }
        }
        return selected;
    }

    function createInvoice(group, period) {
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

        const totals = group.charges.reduce((out, row) => {
            out[row.code] = money(number(out[row.code]) + row.amount);
            return out;
        }, {});
        Object.keys(totals).sort().forEach((code, line) => {
            if (code === 'OF4' || !totals[code]) return;
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'item', line, value: CONFIG.INVOICE_ITEMS[code] });
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'quantity', line, value: 1 });
            invoice.setSublistValue({ sublistId: 'item', fieldId: 'rate', line, value: totals[code] });
            const refs = [...new Set(group.charges.filter(row => row.code === code).map(row => row.sourceText).filter(Boolean))];
            invoice.setSublistValue({
                sublistId: 'item', fieldId: 'description', line,
                value: `${code} - ${CONFIG.DESCRIPTIONS[code]}${refs.length ? ` (${refs.join(', ')})` : ''}`.slice(0, 999)
            });
        });
        return String(invoice.save({ enableSourcing: true, ignoreMandatoryFields: false }));
    }

    function markSourceTransactions(group, invoiceId) {
        const unique = {};
        group.charges.filter(row => row.sourceType === record.Type.PURCHASE_ORDER || row.sourceType === record.Type.SALES_ORDER)
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
        let model = collectModel(period, customerId);
        let message = '';

        if (context.request.method === 'POST') {
            const selected = selectedGroupKeys(context.request);
            if (selected.size) {
                const created = [];
                selected.forEach(key => {
                    const group = model.groups[key];
                    if (!group) throw new Error(`Customer group ${key} is no longer eligible. Refresh and review again.`);
                    const invoiceId = createInvoice(group, period);
                    markSourceTransactions(group, invoiceId);
                    created.push({ invoiceId, amount: group.total });
                });
                message = `Created ${created.length} open invoice(s), total ${money(created.reduce((sum, row) => sum + row.amount, 0)).toFixed(2)}.`;
                model = collectModel(period, customerId);
            } else {
                message = 'Filters applied. No invoices were created.';
            }
        }

        const invalidColumnNotes = Object.keys(model.diagnostics && model.diagnostics.invalidColumns || {})
            .map(type => ({ type, columns: [...model.diagnostics.invalidColumns[type]] }))
            .filter(entry => entry.columns.length)
            .map(entry => `${entry.type}: ${entry.columns.join(', ')}`);
        if (invalidColumnNotes.length) {
            message = `Warning: these fields are invalid search columns on the noted transaction type right now — likely missing, or Applies To/sourcing config doesn't cover that type — so they were skipped this run (amounts sourced from them read as 0; if the skipped field is "${CONFIG.SOURCE_INVOICE_FIELD}", duplicate-invoice protection is also OFF). Fix them in NetSuite, then re-run. ${invalidColumnNotes.join(' | ')} ${message}`;
        }

        context.response.writePage(buildForm(period, customerId, model, message));
    }

    return { onRequest };
});
