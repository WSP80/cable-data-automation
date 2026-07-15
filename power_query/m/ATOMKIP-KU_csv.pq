let
    SourceFolder = "D:\Weiterbildung\6.PortfolioProject\data\raw\ATOMKIP-KU\csv",

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
        "",
        "Марка",
        "Цена без НДС, руб./км"
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
                        "Datei transformieren (4)",
                        each try #"Datei transformieren (4)"([Content]) otherwise null
                    ),

                #"Umbenannte Spalten1" =
                    Table.RenameColumns(
                        #"Benutzerdefinierte Funktion aufrufen1",
                        {{"Name", "Source.Name"}}
                    ),

                #"Andere entfernte Spalten1" =
                    Table.SelectColumns(
                        #"Umbenannte Spalten1",
                        {"Source.Name", "Datei transformieren (4)"}
                    ),

                #"Entfernte Fehler1" =
                    Table.SelectRows(
                        #"Andere entfernte Spalten1",
                        each [#"Datei transformieren (4)"] <> null
                    ),

                Expanded =
                    if Table.IsEmpty(#"Entfernte Fehler1") then
                        EmptyResult
                    else
                        let
                            #"Erweiterte Tabellenspalte1" =
                                Table.ExpandTableColumn(
                                    #"Entfernte Fehler1",
                                    "Datei transformieren (4)",
                                    TransformColumns,
                                    TransformColumns
                                ),

                            #"Geänderter Typ" =
                                Table.TransformColumnTypes(
                                    #"Erweiterte Tabellenspalte1",
                                    {{"", type date}}
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

                            #"Umbenannte Spalten2" =
                                Table.RenameColumns(
                                    #"Hinzugefügte benutzerdefinierte Spalte",
                                    {{"Benutzerdefiniert", "invoice_number"}}
                                ),

                            #"Neu angeordnete Spalten" =
                                Table.ReorderColumns(
                                    #"Umbenannte Spalten2",
                                    {
                                        "source_file",
                                        "invoice_number",
                                        "",
                                        "Марка",
                                        "Цена без НДС, руб./км"
                                    }
                                ),

                            #"Umbenannte Spalten3" =
                                Table.RenameColumns(
                                    #"Neu angeordnete Spalten",
                                    {
                                        {"", "invoice_date"},
                                        {"Марка", "product_description"}
                                    }
                                ),

                            #"Geänderter Typ1" =
                                Table.TransformColumnTypes(
                                    #"Umbenannte Spalten3",
                                    {{"Цена без НДС, руб./км", type number}}
                                ),

                            #"Hinzugefügte benutzerdefinierte Spalte1" =
                                Table.AddColumn(
                                    #"Geänderter Typ1",
                                    "length_km",
                                    each null,
                                    type nullable number
                                ),

                            #"Neu angeordnete Spalten1" =
                                Table.ReorderColumns(
                                    #"Hinzugefügte benutzerdefinierte Spalte1",
                                    {
                                        "source_file",
                                        "invoice_number",
                                        "invoice_date",
                                        "product_description",
                                        "length_km",
                                        "Цена без НДС, руб./км"
                                    }
                                ),

                            #"Umbenannte Spalten4" =
                                Table.RenameColumns(
                                    #"Neu angeordnete Spalten1",
                                    {{"Цена без НДС, руб./км", "unit_price_excl_vat"}}
                                ),

                            #"Hinzugefügte benutzerdefinierte Spalte2" =
                                Table.AddColumn(
                                    #"Umbenannte Spalten4",
                                    "comment",
                                    each null,
                                    type nullable text
                                ),

                            #"Gefilterte Zeilen" =
                                Table.SelectRows(
                                    #"Hinzugefügte benutzerdefinierte Spalte2",
                                    each [product_description] <> null
                                        and (
                                            Text.Contains([product_description], "АТОМКИП-КУ")
                                            or Text.Contains([product_description], "ATOMKIP-KU")
                                        )
                                ),

                            #"Ersetzter Wert" =
                                Table.ReplaceValue(
                                    #"Gefilterte Zeilen",
                                    "кл5690",
                                    "кл5 690",
                                    Replacer.ReplaceText,
                                    {"product_description"}
                                ),

                            #"Ersetzter Wert1" =
                                Table.ReplaceValue(
                                    #"Ersetzter Wert",
                                    "kl5690",
                                    "kl5 690",
                                    Replacer.ReplaceText,
                                    {"product_description"}
                                ),

                            #"Geänderter Typ2" =
                                Table.TransformColumnTypes(
                                    #"Ersetzter Wert1",
                                    {
                                        {"length_km", type number},
                                        {"unit_price_excl_vat", type number}
                                    }
                                )
                        in
                            #"Geänderter Typ2"
            in
                Expanded
in
    Result