//%attributes = {"invisible":true}
// (P) Clients_Reorder
ORDER BY:C49([CLIENTS:1]; [CLIENTS:1]Name:2; >)

infoClients:=Replace string(Replace string(Get localized string:C991("Runtime_CountClients"); "{selected}"; String:C10(Records in selection:C76([CLIENTS:1]))); "{total}"; String:C10(Records in table:C83([CLIENTS:1])))

UPDATE_ALL_BUTTON("bAllClients"; Current form table:C627)

UPDATE_SUBSET_BUTTON("bShowSubsetClients"; "$highlightedClients"; Current form table:C627)

