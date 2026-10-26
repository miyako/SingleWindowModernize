//%attributes = {"invisible":true}
// (P) Invoices_Reorder
ORDER BY:C49([INVOICES:2]; [INVOICES:2]Date:4; <)

infoInvoices:=Replace string(Replace string(Get localized string:C991("Runtime_CountInvoices"); "{selected}"; String:C10(Records in selection:C76([INVOICES:2]))); "{total}"; String:C10(Records in table:C83([INVOICES:2])))

UPDATE_ALL_BUTTON("bAllInvoices"; Current form table:C627)

UPDATE_SUBSET_BUTTON("bShowSubsetInvoices"; "$highlightedInvoices"; Current form table:C627)