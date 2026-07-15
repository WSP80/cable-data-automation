let
    Quelle = Folder.Files("D:\Weiterbildung\6.PortfolioProject\data\raw\MK\pdf\"),

    NurPDF = Table.SelectRows(
        Quelle,
        each Text.Lower([Extension]) = ".pdf"
    ),

    MitDaten = Table.AddColumn(
        NurPDF,
        "Data",
        each fnParseMK([Content], [Name]),
        type table
    ),

    Expand = Table.ExpandTableColumn(
        MitDaten,
        "Data",
        {
            "Номер КП",
            "Дата КП",
            "Наименование продукции",
            "Количество",
            "Цена без учета#(lf)НДС, руб",
            "Комментарий"
        },
        {
            "invoice_number",
            "invoice_date",
            "product_description",
            "length_km",
            "unit_price_excl_vat",
            "comment_raw"
        }
    ),

    #"Source File" = Table.RenameColumns(
        Expand,
        {
            {"Name", "source_file"}
        }
    ),

    #"Ausgewählte Spalten" = Table.SelectColumns(
        #"Source File",
        {
            "source_file",
            "invoice_number",
            "invoice_date",
            "product_description",
            "length_km",
            "unit_price_excl_vat"
        }
    ),

    #"Comment hinzugefügt" = Table.AddColumn(
        #"Ausgewählte Spalten",
        "comment",
        each null,
        type text
    ),

    #"Text bereinigt" = Table.TransformColumns(
        #"Comment hinzugefügt",
        {
            {"product_description", each if _ = null then null else Text.Clean(Text.Trim(Text.From(_))), type text}
        }
    ),

    #"Datentypen" = Table.TransformColumnTypes(
        #"Text bereinigt",
        {
            {"source_file", type text},
            {"invoice_number", type text},
            {"invoice_date", type date},
            {"product_description", type text},
            {"length_km", type number},
            {"unit_price_excl_vat", type number},
            {"comment", type text}
        },
        "ru-RU"
    ),

    #"Neu angeordnete Spalten" = Table.ReorderColumns(
        #"Datentypen",
        {
            "source_file",
            "invoice_number",
            "invoice_date",
            "product_description",
            "length_km",
            "unit_price_excl_vat",
            "comment"
        }
    ),
    #"Geänderter Typ" = Table.TransformColumnTypes(#"Neu angeordnete Spalten",{{"invoice_date", type date}})
in
    #"Geänderter Typ"