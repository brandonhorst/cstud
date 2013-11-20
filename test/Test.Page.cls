Class Test.Class Extends %ZEN.Component.page
{

Parameter JSINCLUDES = "/csp/user/brandonLaunchPopupWindow.js";

/// This XML block defines the contents of this page.
XData Contents [ XMLNamespace = "http://www.intersystems.com/zen" ]
{
<page xmlns="http://www.intersystems.com/zen" title="">
<button caption="Post-2011.1" onclick="zenPage.launchPopupWindow('Test.Page.cls')" />
<button caption="Pre-2011.1" onclick="zenPage.myThing()" />
<button caption="Fire" onclick="zenPage.firePopupAction('test','sports' )" />
</page>
}

ClientMethod myThing() [ Language = javascript ]
{
    brandonLaunchPopupWindow('Test.SubPage.cls','Select Company','status,scrollbars,width=600,height=500')
}

ClientMethod onPopupAction(popupName, action, value) [ Language = javascript ]
{
    alert(popupName + " " + action + " " + value);
}

}
