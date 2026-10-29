//%attributes = {"invisible":true}
// (P) Products_Reorder
ORDER BY:C49([PRODUCTS:4]; [PRODUCTS:4]Reference:2; >)

infoProducts:=Replace string(Replace string(Get localized string:C991("Runtime_CountProducts"); "{selected}"; String:C10(Records in selection:C76([PRODUCTS:4]))); "{total}"; String:C10(Records in table:C83([PRODUCTS:4])))

UPDATE_ALL_BUTTON("bAllProducts"; Current form table:C627)

UPDATE_SUBSET_BUTTON("bShowSubsetProducts"; "$highlightedProducts"; Current form table:C627)