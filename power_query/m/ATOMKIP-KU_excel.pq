let
    SourceFolder = "D:\Weiterbildung\6.PortfolioProject\data\raw\ATOMKIP-KU\excel",

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
            invoice_number = text,
            invoice_date = date,
            product_description = text,
            length_km = nullable number,
            unit_price_excl_vat = nullable number,
            comment = nullable text
        ],
        {}
    ),

    TransformColumns = {
        "Column1",
        "Column2",
        "Column3",
        "Column4",
        "Column5",
        "Column6",
        "Column7",
        "Column8",
        "Column9"
    },

    Quelle = try Folder.Files(SourceFolder) otherwise EmptySource,
    #"Gefilterte ausgeblendete Dateien1" = Table.SelectRows(Quelle, each [Attributes]?[Hidden]? <> true),

    Result =
        if Table.IsEmpty(#"Gefilterte ausgeblendete Dateien1") then
            EmptyResult
        else
            let
                #"Benutzerdefinierte Funktion aufrufen1" = Table.AddColumn(#"Gefilterte ausgeblendete Dateien1", "Datei transformieren", each #"Datei transformieren"([Content])),
                #"Umbenannte Spalten1" = Table.RenameColumns(#"Benutzerdefinierte Funktion aufrufen1", {{"Name", "Source.Name"}}),
                #"Dateiname duplizieren" = Table.DuplicateColumn(#"Umbenannte Spalten1", "Source.Name", "source_file"),
                #"Andere entfernte Spalten1" = Table.SelectColumns(#"Dateiname duplizieren", {"Source.Name", "source_file", "Datei transformieren"}),
                #"Erweiterte Tabellenspalte1" = Table.ExpandTableColumn(#"Andere entfernte Spalten1", "Datei transformieren", TransformColumns, TransformColumns),
                #"Geänderter Typ" = Table.TransformColumnTypes(#"Erweiterte Tabellenspalte1",{{"Source.Name", type text}, {"source_file", type text}, {"Column1", type text}, {"Column2", type text}, {"Column3", type any}, {"Column4", type any}, {"Column5", type any}, {"Column6", type any}, {"Column7", type text}, {"Column8", type any}, {"Column9", type any}}),
                #"Andere entfernte Spalten" = Table.SelectColumns(#"Geänderter Typ",{"source_file", "Source.Name", "Column2", "Column3", "Column4", "Column6"}),
                #"Gefilterte Zeilen" = Table.SelectRows(#"Andere entfernte Spalten", each Text.Contains([Column2], "АТОМКИП-КУ") or Text.Contains([Column2], "ATOMKIP-KU")),
                Divisionsspalte = Table.TransformColumns(#"Gefilterte Zeilen", {{"Column4", each _ / 1.22, type number}}),
                #"Ersetzter Wert" = Table.ReplaceValue(Divisionsspalte,"КП для ПромИК ПВГ ООО ","",Replacer.ReplaceText,{"Source.Name"}),
                #"Spalte nach Trennzeichen teilen" = Table.SplitColumn(#"Ersetzter Wert", "Source.Name", Splitter.SplitTextByDelimiter(" от ", QuoteStyle.Csv), {"Source.Name.1", "Source.Name.2"}),
                #"Ersetzter Wert1" = Table.ReplaceValue(#"Spalte nach Trennzeichen teilen",".xlsx","",Replacer.ReplaceText,{"Source.Name.2"}),
                #"Spalte nach Trennzeichen teilen1" = Table.SplitColumn(#"Ersetzter Wert1", "Source.Name.2", Splitter.SplitTextByDelimiter("г", QuoteStyle.Csv), {"Source.Name.2.1", "Source.Name.2.2"}),
                #"Geänderter Typ1" = Table.TransformColumnTypes(#"Spalte nach Trennzeichen teilen1",{{"Source.Name.1", type text}, {"Source.Name.2.1", type text}, {"Source.Name.2.2", type text}}),
                #"Entfernte Spalten" = Table.RemoveColumns(#"Geänderter Typ1",{"Source.Name.2.2"}),
                #"Geänderter Typ mit Gebietsschema" = Table.TransformColumnTypes(#"Entfernte Spalten", {{"Source.Name.2.1", type date}}, "ru-RU"),
                #"Umbenannte Spalten" = Table.RenameColumns(#"Geänderter Typ mit Gebietsschema",{{"Source.Name.1", "invoice_number"}, {"Source.Name.2.1", "invoice_date"}, {"Column2", "product_description"}, {"Column3", "length_km"}, {"Column4", "unit_price_excl_vat"}, {"Column6", "comment"}}),
                #"Neu angeordnete Spalten" = Table.ReorderColumns(#"Umbenannte Spalten",{"source_file", "invoice_number", "invoice_date", "product_description", "length_km", "unit_price_excl_vat", "comment"}),
                #"Gefilterte Zeilen1" = Table.SelectRows(#"Neu angeordnete Spalten", each Text.Contains([product_description], "АТОМКИП-КУ") or Text.Contains([product_description], "ATOMKIP-KU")),
                #"Ersetzter Wert2" = Table.ReplaceValue(#"Gefilterte Zeilen1","кл5690","кл5 690",Replacer.ReplaceText,{"product_description"}),
                #"Geänderter Typ2" = Table.TransformColumnTypes(#"Ersetzter Wert2",{{"length_km", type number}})
            in
                #"Geänderter Typ2"
in
    Result