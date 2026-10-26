//%attributes = {"invisible":true}
var $result : Object:=New object("failures"; New collection)
var $data : Object:=New object
var $setup : cs.Toolbar_Setup
var $saved; $settings : Collection
var $reference : Integer
var $caption : Text

SET DATABASE LOCALIZATION("ja"; *)
FORM LOAD("Toolbar_Setup"; $data)
$data.userlist:=New list
$setup:=cs.Toolbar_Setup.new(Get 4D folder(Current resources folder)+"Images"+Folder separator+"Buttons_32"+Folder separator)
$setup.add("Name"; 101; "New_32.png")
$setup.add("City"; 101001; "Query_32.png")
$settings:=New collection(New object("id"; 101; "name"; "Name"; "sub"; New collection(New object("id"; 101001; "name"; "City"))))
$setup.setUserSettings($settings)
GET LIST ITEM($data.userlist; 1; $reference; $caption)
$result.displayedCaption:=$caption
If ($caption#"名称")
	$result.failures.push("Toolbar setup did not display its Japanese caption")
End if
$saved:=$setup.storeSettings()
$result.saved:=$saved
If (($saved.length#1) | ($saved[0].name#"Name") | ($saved[0].sub[0].name#"City"))
	$result.failures.push("Translated captions replaced canonical action keys")
End if
CLEAR LIST($data.userlist; *)
CLEAR LIST($setup.list; *)
FORM UNLOAD
$result.passed:=($result.failures.length=0)
File("/PACKAGE/agent-test.txt").setText(JSON Stringify($result; *))
QUIT 4D
