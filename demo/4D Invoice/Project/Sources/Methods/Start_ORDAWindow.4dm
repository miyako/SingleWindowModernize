//%attributes = {}
#DECLARE($params : Object)

var $title : Text:=Get localized string:C991("Core_DemoMarker")
var $window : Integer
var $left; $top; $right; $bottom; $i : Integer

If (Count parameters=0)
	CALL WORKER(1; Current method name; {})
Else
	ARRAY LONGINT($windows; 0)
	WINDOW LIST($windows)
	For ($i; 1; Size of array($windows))
		$window:=$windows{$i}
		If ((Window process($window)=1) & (Position($title; Get window title($window))=1))
			GET WINDOW RECT($left; $top; $right; $bottom; $window)
			CALL FORM($window; Formula(SET WINDOW RECT($left; $top; $right; $bottom; $window)))
			return
		End if
	End for
	If (Is Windows:C1573)
		HIDE MENU BAR:C432
	End if
	SET MENU BAR:C67("empty")
	$window:=Open form window:C675("ORDAListbox"; Plain form window no title:K39:19)
	SET WINDOW TITLE($title; $window)
	DIALOG:C40("ORDAListbox"; *)
	CALL FORM($window; Formula(DemoOfferData))
End if