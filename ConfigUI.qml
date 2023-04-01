// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.3
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Convert Image")

    minimumWidth: grid.width + 2 * UM.Theme.getSize("default_margin").height
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height/2
    width: minimumWidth
    height: minimumHeight

    GridLayout
    {
        UM.I18nCatalog { id: catalog; name: "cura" }
        id: grid
        columnSpacing: UM.Theme.getSize("narrow_margin").width
        rowSpacing: UM.Theme.getSize("narrow_margin").height
        columns: 2

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Height (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: peak_height_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.TextField
        {
            id: peak_height
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            selectByMouse: true
            objectName: "Peak_Height"
            validator: RegularExpressionValidator { regularExpression: /^\d{0,3}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onPeakHeightChanged(text)
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The maximum distance of each pixel from \"Base.\"")
            visible: peak_height.hovered || peak_height_label.containsMouse
            targetPoint: Qt.point(peak_height.x + Math.round(peak_height.width / 2), 0)
            y: peak_height.y + peak_height.height + UM.Theme.getSize("default_margin").height
        }


    }

    Item
    {
        ButtonGroup
        {
            buttons: [ok_button, cancel_button]
            checkedButton: ok_button
        }
    }

    onAccepted: manager.onOkButtonClicked()
    onRejected: manager.onCancelButtonClicked()

    buttonSpacing: UM.Theme.getSize("default_margin").width

    rightButtons: [
        Cura.TertiaryButton
        {
            id: cancel_button
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: manager.onCancelButtonClicked()
        },
        Cura.PrimaryButton
        {
            id: ok_button
            text: catalog.i18nc("@action:button", "OK")
            onClicked: manager.onOkButtonClicked()
        }
    ]
}
