// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    width: 350 * Screen.devicePixelRatio;
    minimumWidth: 350 * Screen.devicePixelRatio;

    height: 180 * Screen.devicePixelRatio;           //250
    minimumHeight: 180 * Screen.devicePixelRatio;       //250

    title: catalog.i18nc("@title:window", "Convert Path...")

    GridLayout
    {
        UM.I18nCatalog{id: catalog; name:"cura"}
        anchors.fill: parent;
        Layout.fillWidth: true
        columnSpacing: 16
        rowSpacing: 4
        columns: 1

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The maximum distance of each pixel from \"Base.\"")
            Row {
                width: parent.width



                CheckBox {
                      id: closeTopButtonFace
                      objectName: "closeTopButtonFace"
                      checked: true
                      onClicked: {
                          manager.oncloseTopButtonFaceChanged(checked)

                      }
                      text: catalog.i18nc("@label", "triangulation")

                      style: UM.Theme.styles.checkbox
                  }
            }
        }



    }

    rightButtons: [
        Button
        {
            id:ok_button
            text: catalog.i18nc("@action:button","OK");
            onClicked: { manager.onOkButtonClicked() }
            enabled: true
        },
        Button
        {
            id:cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            onClicked: { manager.onCancelButtonClicked() }
            enabled: true
        }
    ]
}
