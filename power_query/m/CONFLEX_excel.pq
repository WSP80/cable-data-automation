let
    SourceFolder = "D:\Weiterbildung\6.PortfolioProject\data\raw\CONFLEX\excel",

    EmptySource = #table(
        type table [
            Content = binary,
            Name = text,
            Attributes = nullable record
        ],
        {}
    ),

    EmptyResult = #table(
        type table [
            source_file = text,
            invoice_number = nullable text,
            invoice_date = date,
            product_description = text,
            length_km = nullable number,
            unit_price_excl_vat = nullable number,
            comment = nullable text
        ],
        {}
    ),

    TransformColumns = {
        "№",
        "Артикул",
        "Уникальный идентификатор (Номенклатура)",
        "Уникальный идентификатор (Характеристика)",
        "Товар",
        "Column6",
        "Column7"
    },

    Quelle = try Folder.Files(SourceFolder) otherwise EmptySource,

    #"Gefilterte ausgeblendete Dateien1" =
        Table.SelectRows(
            Quelle,
            each [Attributes]?[Hidden]? <> true
        ),

    Result =
        if Table.IsEmpty(#"Gefilterte ausgeblendete Dateien1") then
            EmptyResult
        else
            let
                #"Benutzerdefinierte Funktion aufrufen1" =
                    Table.AddColumn(
                        #"Gefilterte ausgeblendete Dateien1",
                        "Datei transformieren (3)",
                        each #"Datei transformieren (3)"([Content])
                    ),

                #"Umbenannte Spalten1" =
                    Table.RenameColumns(
                        #"Benutzerdefinierte Funktion aufrufen1",
                        {{"Name", "Source.Name"}}
                    ),

                #"Andere entfernte Spalten1" =
                    Table.SelectColumns(
                        #"Umbenannte Spalten1",
                        {"Source.Name", "Datei transformieren (3)"}
                    ),

                #"Erweiterte Tabellenspalte1" =
                    Table.ExpandTableColumn(
                        #"Andere entfernte Spalten1",
                        "Datei transformieren (3)",
                        TransformColumns,
                        TransformColumns
                    ),

                #"Geänderter Typ" =
                    Table.TransformColumnTypes(
                        #"Erweiterte Tabellenspalte1",
                        {
                            {"Source.Name", type text},
                            {"№", Int64.Type},
                            {"Артикул", Int64.Type},
                            {"Уникальный идентификатор (Номенклатура)", type text},
                            {"Уникальный идентификатор (Характеристика)", type text},
                            {"Товар", type text},
                            {"Column6", type any},
                            {"Column7", type text}
                        }
                    ),

                #"Umbenannte Spalten" =
                    Table.RenameColumns(
                        #"Geänderter Typ",
                        {{"Source.Name", "source_file"}}
                    ),

                #"Hinzugefügte benutzerdefinierte Spalte" =
                    Table.AddColumn(
                        #"Umbenannte Spalten",
                        "Benutzerdefiniert",
                        each null
                    ),

                #"Neu angeordnete Spalten" =
                    Table.ReorderColumns(
                        #"Hinzugefügte benutzerdefinierte Spalte",
                        {
                            "source_file",
                            "Benutzerdefiniert",
                            "№",
                            "Артикул",
                            "Уникальный идентификатор (Номенклатура)",
                            "Уникальный идентификатор (Характеристика)",
                            "Товар",
                            "Column6",
                            "Column7"
                        }
                    ),

                #"Umbenannte Spalten2" =
                    Table.RenameColumns(
                        #"Neu angeordnete Spalten",
                        {{"Benutzerdefiniert", "invoice_number"}}
                    ),

                #"Hinzugefügte benutzerdefinierte Spalte1" =
                    Table.AddColumn(
                        #"Umbenannte Spalten2",
                        "invoice_date",
                        each #date(2022, 11, 7),
                        type date
                    ),

                #"Neu angeordnete Spalten1" =
                    Table.ReorderColumns(
                        #"Hinzugefügte benutzerdefinierte Spalte1",
                        {
                            "source_file",
                            "invoice_number",
                            "invoice_date",
                            "№",
                            "Артикул",
                            "Уникальный идентификатор (Номенклатура)",
                            "Уникальный идентификатор (Характеристика)",
                            "Товар",
                            "Column6",
                            "Column7"
                        }
                    ),

                #"Entfernte Spalten" =
                    Table.RemoveColumns(
                        #"Neu angeordnete Spalten1",
                        {
                            "№",
                            "Артикул",
                            "Уникальный идентификатор (Номенклатура)",
                            "Уникальный идентификатор (Характеристика)"
                        }
                    ),

                #"Umbenannte Spalten3" =
                    Table.RenameColumns(
                        #"Entfernte Spalten",
                        {{"Товар", "product_description"}}
                    ),

                #"Gefilterte Zeilen" =
                    Table.SelectRows(
                        #"Umbenannte Spalten3",
                        each [product_description] <> null
                    ),

                #"Duplizierte Spalte" =
                    Table.DuplicateColumn(
                        #"Gefilterte Zeilen",
                        "invoice_number",
                        "invoice_number - Kopie"
                    ),

                #"Umbenannte Spalten4" =
                    Table.RenameColumns(
                        #"Duplizierte Spalte",
                        {{"invoice_number - Kopie", "length_km"}}
                    ),

                #"Neu angeordnete Spalten2" =
                    Table.ReorderColumns(
                        #"Umbenannte Spalten4",
                        {
                            "source_file",
                            "invoice_number",
                            "invoice_date",
                            "product_description",
                            "length_km",
                            "Column6",
                            "Column7"
                        }
                    ),

                #"Umbenannte Spalten5" =
                    Table.RenameColumns(
                        #"Neu angeordnete Spalten2",
                        {{"Column6", "unit_price_excl_vat"}}
                    ),

                #"Entfernte Spalten1" =
                    Table.RemoveColumns(
                        #"Umbenannte Spalten5",
                        {"Column7"}
                    ),

                #"Duplizierte Spalte1" =
                    Table.DuplicateColumn(
                        #"Entfernte Spalten1",
                        "invoice_number",
                        "invoice_number - Kopie"
                    ),

                #"Umbenannte Spalten6" =
                    Table.RenameColumns(
                        #"Duplizierte Spalte1",
                        {{"invoice_number - Kopie", "comment"}}
                    ),

                #"Geänderter Typ1" =
                    Table.TransformColumnTypes(
                        #"Umbenannte Spalten6",
                        {
                            {"invoice_date", type date},
                            {"unit_price_excl_vat", type number},
                            {"length_km", type number}
                        }
                    )
            in
                #"Geänderter Typ1"
in
    Result