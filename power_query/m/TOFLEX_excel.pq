let
    SourceFolder = "D:\Weiterbildung\6.PortfolioProject\data\raw\TOFLEX\excel",

    EmptySource = #table(
        type table [
            Content = binary,
            Name = text,
            Extension = text,
            Attributes = nullable record
        ],
        {}
    ),

    EmptyResult = #table(
        type table [
            source_file = text,
            invoice_number = nullable text,
            invoice_date = nullable date,
            product_description = text,
            length_km = nullable number,
            unit_price_excl_vat = nullable number,
            comment = nullable text
        ],
        {}
    ),

    TransformColumns = List.Transform({1..62}, each "Column" & Text.From(_)),
    EmptyTransformed = #table(TransformColumns, {}),

    CleanText = (value as nullable any) as nullable text =>
        if value = null then
            null
        else
            Text.Trim(Text.Clean(Text.From(value))),

    ToNumber = (value as nullable any) as nullable number =>
        let
            TextValue = CleanText(value),
            CleanValue =
                if TextValue = null then
                    null
                else
                    Text.Replace(
                        Text.Replace(Text.Replace(TextValue, Character.FromNumber(160), ""), " ", ""),
                        ".",
                        ""
                    ),
            Result = try Number.FromText(CleanValue, "ru-RU") otherwise null
        in
            Result,

    ContainsAny = (value as nullable any, patterns as list) as logical =>
        let
            TextValue = if value = null then "" else Text.From(value),
            Result = List.AnyTrue(List.Transform(patterns, each Text.Contains(TextValue, _)))
        in
            Result,

    BeforeAnyDelimiter = (value as nullable any, delimiters as list) as nullable text =>
        let
            TextValue = CleanText(value),
            Matches =
                if TextValue = null then
                    {}
                else
                    List.Select(delimiters, each Text.Contains(TextValue, _)),
            Result =
                if TextValue = null then
                    null
                else if List.IsEmpty(Matches) then
                    TextValue
                else
                    Text.BeforeDelimiter(TextValue, Matches{0})
        in
            Result,

    AfterAnyDelimiter = (value as nullable any, delimiters as list) as nullable text =>
        let
            TextValue = CleanText(value),
            Matches =
                if TextValue = null then
                    {}
                else
                    List.Select(delimiters, each Text.Contains(TextValue, _)),
            Result =
                if TextValue = null or List.IsEmpty(Matches) then
                    null
                else
                    Text.AfterDelimiter(TextValue, Matches{0})
        in
            Result,

    RemoveKnownText = (value as nullable any, replacements as list) as nullable text =>
        let
            TextValue = CleanText(value),
            Result =
                if TextValue = null then
                    null
                else
                    List.Accumulate(
                        replacements,
                        TextValue,
                        (state, current) => Text.Replace(state, current, "")
                    )
        in
            CleanText(Result),

    BrandPatterns = {
        "TOFLEX",
        "ТОФЛЕКС",
        "РўРћР¤Р›Р•РљРЎ",
        "Р СћР С›Р В¤Р вЂєР вЂўР С™Р РЋ"
    },

    InvoicePatterns = {
        "Счет",
        "Счёт",
        "РЎС‡РµС‚",
        "Р РЋРЎвЂЎР ВµРЎвЂљ"
    },

    InvoiceDelimiters = {
        " от ",
        " РѕС‚ ",
        " Р С•РЎвЂљ "
    },

    InvoicePrefixes = {
        "Счет на оплату ",
        "Счёт на оплату ",
        "РЎС‡РµС‚ РЅР° РѕРїР»Р°С‚Сѓ ",
        "Р РЋРЎвЂЎР ВµРЎвЂљ Р Р…Р В° Р С•Р С—Р В»Р В°РЎвЂљРЎС“ "
    },

    CablePrefixes = {
        "Кабель ",
        "РљР°Р±РµР»СЊ ",
        "Р С™Р В°Р В±Р ВµР В»РЎРЉ "
    },

    TuDelimiters = {
        "ТУ",
        "РўРЈ",
        "Р СћР Р€"
    },

    Quelle = try Folder.Files(SourceFolder) otherwise EmptySource,

    VisibleFiles =
        Table.SelectRows(
            Quelle,
            each [Attributes]?[Hidden]? <> true
        ),

    Result =
        if Table.IsEmpty(VisibleFiles) then
            EmptyResult
        else
            let
                AddedData =
                    Table.AddColumn(
                        VisibleFiles,
                        "Datei transformieren (2)",
                        each try #"Datei transformieren (2)"([Content]) otherwise EmptyTransformed,
                        type table
                    ),

                RenamedFileName =
                    Table.RenameColumns(
                        AddedData,
                        {{"Name", "Source.Name"}}
                    ),

                SelectedNested =
                    Table.SelectColumns(
                        RenamedFileName,
                        {"Source.Name", "Datei transformieren (2)"}
                    ),

                Expanded =
                    Table.ExpandTableColumn(
                        SelectedNested,
                        "Datei transformieren (2)",
                        TransformColumns,
                        TransformColumns
                    ),

                SelectedColumns =
                    Table.SelectColumns(
                        Expanded,
                        {
                            "Source.Name",
                            "Column2",
                            "Column4",
                            "Column35",
                            "Column45",
                            "Column62"
                        },
                        MissingField.UseNull
                    ),

                CleanedColumns =
                    Table.TransformColumns(
                        SelectedColumns,
                        {
                            {"Column2", each CleanText(_), type nullable text},
                            {"Column4", each CleanText(_), type nullable text},
                            {"Column35", each ToNumber(_), type nullable number},
                            {"Column45", each ToNumber(_), type nullable number},
                            {"Column62", each CleanText(_), type nullable text}
                        }
                    ),

                AddedInvoiceMarker =
                    Table.AddColumn(
                        CleanedColumns,
                        "invoice_marker",
                        each if ContainsAny([Column2], InvoicePatterns) then [Column2] else null,
                        type nullable text
                    ),

                FilledInvoiceMarker =
                    Table.FillDown(
                        AddedInvoiceMarker,
                        {"invoice_marker"}
                    ),

                RemovedNonProductRows =
                    Table.SelectRows(
                        FilledInvoiceMarker,
                        each [Column4] <> null
                            and [Column4] <> ""
                            and [Column4] <> "7017307579"
                            and not ContainsAny([Column4], {"Товар", "РўРѕРІР°СЂ", "Р СћР С•Р Р†Р В°РЎР‚"})
                    ),

                AddedInvoiceNumber =
                    Table.AddColumn(
                        RemovedNonProductRows,
                        "invoice_number",
                        each RemoveKnownText(BeforeAnyDelimiter([invoice_marker], InvoiceDelimiters), InvoicePrefixes),
                        type nullable text
                    ),

                AddedInvoiceDate =
                    Table.AddColumn(
                        AddedInvoiceNumber,
                        "invoice_date",
                        each try Date.FromText(AfterAnyDelimiter([invoice_marker], InvoiceDelimiters), "ru-RU") otherwise null,
                        type nullable date
                    ),

                RemovedCablePrefix =
                    Table.TransformColumns(
                        AddedInvoiceDate,
                        {
                            {"Column4", each RemoveKnownText(_, CablePrefixes), type nullable text}
                        }
                    ),

                AddedProductDescription =
                    Table.AddColumn(
                        RemovedCablePrefix,
                        "product_description",
                        each BeforeAnyDelimiter([Column4], TuDelimiters),
                        type nullable text
                    ),

                CleanedProductDescription =
                    Table.TransformColumns(
                        AddedProductDescription,
                        {
                            {"product_description", each if _ = null then null else Text.Replace(CleanText(_), "*", "x"), type nullable text}
                        }
                    ),

                RenamedColumns =
                    Table.RenameColumns(
                        CleanedProductDescription,
                        {
                            {"Source.Name", "source_file"},
                            {"Column35", "length_km"},
                            {"Column45", "unit_price_excl_vat"},
                            {"Column62", "comment"}
                        }
                    ),

                SelectedFinalColumns =
                    Table.SelectColumns(
                        RenamedColumns,
                        {
                            "source_file",
                            "invoice_number",
                            "invoice_date",
                            "product_description",
                            "length_km",
                            "unit_price_excl_vat",
                            "comment"
                        },
                        MissingField.UseNull
                    ),

                ProductRows =
                    Table.SelectRows(
                        SelectedFinalColumns,
                        each [product_description] <> null
                            and [product_description] <> ""
                            and [length_km] <> null
                            and [unit_price_excl_vat] <> null
                    ),

                BrandRows =
                    Table.SelectRows(
                        ProductRows,
                        each ContainsAny([product_description], BrandPatterns)
                    ),

                FinalRows =
                    if Table.IsEmpty(BrandRows) then
                        ProductRows
                    else
                        BrandRows,

                FinalTypes =
                    Table.TransformColumnTypes(
                        FinalRows,
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
                    )
            in
                FinalTypes
in
    Result