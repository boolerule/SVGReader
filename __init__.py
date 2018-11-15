# Copyright (c) 2017 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from . import SVGReader

##  为插件定义额外的元数据。
#
#   文件阅读器类型插件必须指定一些附加的元数据
#   能够读取的文件类型
#  某些类型的插件需要其他元数据，例如哪些文件类型
# ＃他们能够阅读或他们定义的工具的名称。 如果是
# ＃“扩展”类型的插件，虽然没有其他元数据。
def getMetaData():
    return {
        "mesh_reader": [ #一个阅读器可能能够读取多个文件类型，所以这是一个列表。
            {
                "extension": "svg",
                "description": "svg file type"
            }
        ]
    }

##  让铀知道这个插件存在。
#
#   在启动应用程序以查找哪些插件时调用此方法
# ＃存在以及它们的类型。 我们需要返回一个字典映射
# ＃表示对象的插件类型（在本例中为“扩展名”）的字符串
# ＃继承自PluginObject。
#
#   \param app 插件需要注册的应用程序。
def register(app):
    return {"mesh_reader": SVGReader.SVGFileReader()}
