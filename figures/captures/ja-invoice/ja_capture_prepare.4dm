//%attributes = {"invisible":true}
var $job : Object:=JSON Parse(File("/PACKAGE/capture-job.json").getText())
If ($job.form="ORDAListbox")
	var $left; $top; $right; $bottom; $delta : Integer
	OBJECT GET COORDINATES(*; "Splitter"; $left; $top; $right; $bottom)
	$delta:=$job.splitterLeft-$left
	OBJECT MOVE(*; "Splitter"; $delta; 0)
	OBJECT MOVE(*; "Listbox"; 0; 0; $delta; 0)
	OBJECT MOVE(*; "buttonsubform"; 0; 0; $delta; 0)
	OBJECT MOVE(*; "preview"; $delta; 0; -$delta; 0)
	Form.toolbar.resize()
	Form.ORDA_listbox.resize()
End if
If (Form.__preview)
	Form.SelectedElement:=Form.listbox.first()
	Form.SelectedPosition:=1
	LISTBOX SELECT ROW(*; "Listbox"; 1; lk replace selection)
	Form.preview.data:=Form.SelectedElement
	Form.preview.Position:=1
	EXECUTE METHOD IN SUBFORM("preview"; Formula(ORDA_Listbox_Method("preview")))
End if
CALL FORM(Current form window; Formula(goto_page_then_screenshot))
