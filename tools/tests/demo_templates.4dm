//%attributes = {"invisible":true}
var $result : Object:=New object("failures"; New collection)
var $value : Object
var $template : cs.Document_TemplatesEntity

SET DATABASE LOCALIZATION("ja"; *)
ds.Document_Templates.writeData("LocaleRegression"; New object("label"; "日本語テンプレート"))
$value:=ds.Document_Templates.readData("LocaleRegression")
If ($value.label#"日本語テンプレート")
	$result.failures.push("Template data was not created as an entity")
End if
ds.Document_Templates.writeData("LocaleRegression"; New object("label"; "更新済み"))
$value:=ds.Document_Templates.readData("LocaleRegression")
If (($value.label#"更新済み") | (ds.Document_Templates.query("Name = :1"; "LocaleRegression").length#1))
	$result.failures.push("Template update duplicated or failed to update the entity")
End if

$template:=ds.Document_Templates.query("Name = :1"; "LocaleRegression").first()
If ($template.data.label#"更新済み")
	$result.failures.push("Template selection did not return the updated entity")
End if
$result.passed:=($result.failures.length=0)
File("/PACKAGE/agent-test.txt").setText(JSON Stringify($result; *))
QUIT 4D
