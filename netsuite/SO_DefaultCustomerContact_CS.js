/**
 * @NApiVersion 2.1
 * @NScriptType ClientScript
 * @NModuleScope SameAccount
 */
define(['N/search'], (search) => {
    // TODO: replace with the real script IDs
    const SO_CONTACT_FIELD = 'custbody_customer_contact'; // "Customer Contact" on the Sales Order
    const DEFAULT_FLAG     = 'custentity_default_contact'; // "Default Contact" checkbox on the Contact

    let mode;

    const pageInit = (ctx) => { mode = ctx.mode; };

    // postSourcing runs after NetSuite has finished sourcing the customer's
    // dependent fields, so the contact list is already filtered to this customer.
    const postSourcing = (ctx) => {
        if (ctx.fieldId !== 'entity') return;
        if (!['create', 'copy'].includes(mode)) return; // don't touch saved orders

        const rec = ctx.currentRecord;
        const customerId = rec.getValue({ fieldId: 'entity' });
        if (!customerId) return;

        const hits = search.create({
            type: search.Type.CONTACT,
            filters: [
                ['company', 'anyof', customerId], 'AND',
                [DEFAULT_FLAG, 'is', 'T'], 'AND',
                ['isinactive', 'is', 'F']
            ],
            columns: [search.createColumn({ name: 'internalid', sort: search.Sort.ASC })]
        }).run().getRange({ start: 0, end: 1 });

        if (hits.length) {
            rec.setValue({ fieldId: SO_CONTACT_FIELD, value: hits[0].id, ignoreFieldChange: true });
        }
    };

    return { pageInit, postSourcing };
});
