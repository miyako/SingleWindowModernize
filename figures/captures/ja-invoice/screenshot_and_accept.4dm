//%attributes = {"invisible":true}
// Called via CALL FORM inside a DIALOG context.
// Takes a screenshot, saves to disk, then accepts and quits.

var $screenshotPath : Text
$screenshotPath:=Form.__screenshotPath

If ($screenshotPath#"")
	var $screenshot : Picture
	FORM SCREENSHOT($screenshot)

	var $file : 4D.File
	$file:=File($screenshotPath)
	$file.parent.create()
	WRITE PICTURE FILE($file.platformPath; $screenshot)
End if

File("/PACKAGE/output/window-ready.txt").setText("ready")
var $attempt : Integer
While ((Not(File("/PACKAGE/output/window-captured.txt").exists)) & ($attempt<600))
	DELAY PROCESS(Current process; 6)
	$attempt:=$attempt+1
End while

ACCEPT
QUIT 4D
