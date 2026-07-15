let
    DataRoot = "D:\Weiterbildung\6.PortfolioProject\data\raw\ATOMKIP-KU",
    TargetFolder = "D:\Weiterbildung\6.PortfolioProject\data\raw\ATOMKIP-KU\pdf\",

    EmptySource = #table(
        type table [
            Content = binary,
            Name = text,
            Extension = text,
            #"Folder Path" = text,
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

    EmptyPdfRows = #table(
        type table [
            product_description = text,
            length_km = nullable any,
            unit_price_incl_vat = nullable any,
            comment = nullable text
        ],
        {}
    ),

    MonthMap = #table(
        type table [
            month_name = text,
            month_number = number
        ],
        {
            {"января", 1}, {"январь", 1}, {"СЏРЅРІР°СЂСЏ", 1}, {"СЏРЅРІР°СЂСЊ", 1},
            {"февраля", 2}, {"февраль", 2}, {"С„РµРІСЂР°Р»СЏ", 2}, {"С„РµРІСЂР°Р»СЊ", 2},
            {"марта", 3}, {"март", 3}, {"РјР°СЂС‚Р°", 3}, {"РјР°СЂС‚", 3},
            {"апреля", 4}, {"апрель", 4}, {"Р°РїСЂРµР»СЏ", 4}, {"Р°РїСЂРµР»СЊ", 4},
            {"мая", 5}, {"май", 5}, {"РјР°СЏ", 5}, {"РјР°Р№", 5},
            {"июня", 6}, {"июнь", 6}, {"РёСЋРЅСЏ", 6}, {"РёСЋРЅСЊ", 6},
            {"июля", 7}, {"июль", 7}, {"РёСЋР»СЏ", 7}, {"РёСЋР»СЊ", 7},
            {"августа", 8}, {"август", 8}, {"Р°РІРіСѓСЃС‚Р°", 8}, {"Р°РІРіСѓСЃС‚", 8},
            {"сентября", 9}, {"сентябрь", 9}, {"СЃРµРЅС‚СЏР±СЂСЏ", 9}, {"СЃРµРЅС‚СЏР±СЂСЊ", 9},
            {"октября", 10}, {"октябрь", 10}, {"РѕРєС‚СЏР±СЂСЏ", 10}, {"РѕРєС‚СЏР±СЂСЊ", 10},
            {"ноября", 11}, {"ноябрь", 11}, {"РЅРѕСЏР±СЂСЏ", 11}, {"РЅРѕСЏР±СЂСЊ", 11},
            {"декабря", 12}, {"декабрь", 12}, {"РґРµРєР°Р±СЂСЏ", 12}, {"РґРµРєР°Р±Р»СЊ", 12}
        }
    ),

    CleanText = (txt as nullable any) as nullable text =>
        if txt = null then
            null
        else
            let
                SourceText = Text.From(txt),
                ReplaceLineBreaks = Text.Replace(Text.Replace(Text.Replace(Text.Replace(SourceText, "#(cr)#(lf)", " "), "#(cr)", " "), "#(lf)", " "), "#(tab)", " "),
                ReplaceNbsp = Text.Replace(ReplaceLineBreaks, Character.FromNumber(160), " "),
                Cleaned = Text.Clean(ReplaceNbsp),
                Trimmed = Text.Trim(Cleaned),
                RemoveDoubleSpaces = List.Accumulate({1..10}, Trimmed, (state, current) => Text.Replace(state, "  ", " "))
            in
                RemoveDoubleSpaces,

    ToNumber = (value as nullable any) as nullable number =>
        let
            TextValue = if value = null then null else Text.Trim(Text.Replace(Text.From(value), Character.FromNumber(160), " ")),
            CleanValue = if TextValue = null then null else Text.Replace(Text.Replace(TextValue, " ", ""), ".", ""),
            Result = try Number.FromText(CleanValue, "ru-RU") otherwise null
        in
            Result,

    MonthNumberFromText = (monthText as nullable text) as nullable number =>
        let
            CleanMonth = if monthText = null then null else Text.Lower(Text.Trim(monthText)),
            FoundRows = if CleanMonth = null then #table({"month_name", "month_number"}, {}) else Table.SelectRows(MonthMap, each [month_name] = CleanMonth),
            Result = if Table.IsEmpty(FoundRows) then null else FoundRows{0}[month_number]
        in
            Result,

    GetDateFromText = (dateText as nullable any) as nullable date =>
        let
            RawText = CleanText(dateText),

            CleanDateText =
                if RawText = null then
                    null
                else
                    Text.Trim(
                        Text.Replace(
                            Text.Replace(
                                Text.Replace(
                                    Text.Replace(
                                        Text.Replace(
                                            Text.Replace(RawText, Character.FromNumber(160), " "),
                                            " г.",
                                            ""
                                        ),
                                        " г",
                                        ""
                                    ),
                                    " Рі.",
                                    ""
                                ),
                                " Рі",
                                ""
                            ),
                            "_",
                            ""
                        )
                    ),

            DirectDate =
                if CleanDateText = null then
                    null
                else
                    try Date.FromText(CleanDateText, "ru-RU") otherwise null,

            CleanWithoutDots =
                if CleanDateText = null then
                    null
                else
                    Text.Trim(Text.Replace(CleanDateText, ".", "")),

            Parts =
                if CleanWithoutDots = null then
                    {}
                else
                    List.Select(Text.Split(CleanWithoutDots, " "), each _ <> ""),

            Day =
                if List.Count(Parts) >= 1 then
                    try Number.FromText(Parts{0}) otherwise null
                else
                    null,

            Month =
                if List.Count(Parts) >= 2 then
                    MonthNumberFromText(Parts{1})
                else
                    null,

            Year =
                if List.Count(Parts) >= 3 then
                    try Number.FromText(Parts{2}) otherwise null
                else
                    null,

            ParsedDate =
                if Day <> null and Month <> null and Year <> null then
                    #date(Year, Month, Day)
                else
                    null,

            Result =
                if DirectDate <> null then
                    DirectDate
                else
                    ParsedDate
        in
            Result,

    ProcessPdfTable = (tbl as table) as table =>
        let
            SelectedColumns = Table.SelectColumns(tbl, {"Column2", "Column3", "Column4", "Column6"}, MissingField.UseNull),

            CleanedColumns = Table.TransformColumns(
                SelectedColumns,
                {
                    {"Column2", each CleanText(_), type text},
                    {"Column6", each CleanText(_), type text}
                }
            ),

            WithIndex = Table.AddIndexColumn(CleanedColumns, "RowIndex", 0, 1, Int64.Type),

            HeaderRows = Table.SelectRows(
                WithIndex,
                each [Column2] <> null
                    and (
                        Text.Contains(Text.Lower([Column2]), "наименование")
                        or Text.Contains([Column2], "РќР°РёРјРµРЅРѕРІР°РЅРёРµ")
                        or Text.Contains([Column2], "Р СњР В°Р С‘Р С")
                    )
            ),

            HeaderIndex = if Table.RowCount(HeaderRows) > 0 then HeaderRows{0}[RowIndex] else null,

            DataRows = if HeaderIndex <> null then Table.SelectRows(WithIndex, each [RowIndex] > HeaderIndex) else WithIndex,

            RemovedIndex = Table.RemoveColumns(DataRows, {"RowIndex"}),

            RenamedColumns = Table.RenameColumns(
                RemovedIndex,
                {
                    {"Column2", "product_description"},
                    {"Column3", "length_km"},
                    {"Column4", "unit_price_incl_vat"},
                    {"Column6", "comment"}
                }
            ),

            FilteredRows = Table.SelectRows(
                RenamedColumns,
                each [product_description] <> null
                    and [product_description] <> ""
                    and not Text.Contains(Text.Lower([product_description]), "итого")
                    and not Text.Contains(Text.Lower([product_description]), "наименование")
                    and not Text.Contains([product_description], "РРўРћР“Рћ")
                    and not Text.Contains([product_description], "РќР°РёРјРµРЅРѕРІР°РЅРёРµ")
                    and not Text.Contains([product_description], "Р ВР СћР С›")
            )
        in
            FilteredRows,

    ProcessPdfFile = (fileContent as binary, fileName as text) as table =>
        let
            NameWithoutExtension = Text.BeforeDelimiter(fileName, ".pdf", {0, RelativePosition.FromEnd}),

            NumberText =
                let
                    Try1 = try Text.BetweenDelimiters(NameWithoutExtension, "№", " от ") otherwise null,
                    Try2 = try Text.BetweenDelimiters(NameWithoutExtension, "в„–", " РѕС‚ ") otherwise null,
                    Try3 = try Text.BetweenDelimiters(NameWithoutExtension, "РІвЂћвЂ“", " Р С•РЎвЂљ ") otherwise null
                in
                    if Try1 <> null then Try1 else if Try2 <> null then Try2 else Try3,

            DateText =
                let
                    Try1 = try Text.AfterDelimiter(NameWithoutExtension, " от ") otherwise null,
                    Try2 = try Text.AfterDelimiter(NameWithoutExtension, " РѕС‚ ") otherwise null,
                    Try3 = try Text.AfterDelimiter(NameWithoutExtension, " Р С•РЎвЂљ ") otherwise null
                in
                    if Try1 <> null then Try1 else if Try2 <> null then Try2 else Try3,

            DocumentDate = GetDateFromText(DateText),

            PdfSource = Pdf.Tables(fileContent, [Implementation = "1.3"]),

            PdfTables = Table.SelectRows(PdfSource, each [Kind] = "Table"),

            ProcessedTables = List.Transform(PdfTables[Data], each ProcessPdfTable(_)),

            CombinedPages = if List.IsEmpty(ProcessedTables) then EmptyPdfRows else Table.Combine(ProcessedTables),

            ConvertedColumns = Table.TransformColumns(
                CombinedPages,
                {
                    {"product_description", each CleanText(_), type text},
                    {"length_km", each ToNumber(_), type nullable number},
                    {"unit_price_incl_vat", each ToNumber(_), type nullable number},
                    {"comment", each CleanText(_), type text}
                }
            ),

            RemovedNullQuantity = Table.SelectRows(ConvertedColumns, each [length_km] <> null),

            PriceWithoutVat = Table.TransformColumns(RemovedNullQuantity, {{"unit_price_incl_vat", each _ / 1.22, type number}}),

            RenamedPrice = Table.RenameColumns(PriceWithoutVat, {{"unit_price_incl_vat", "unit_price_excl_vat"}}),

            AddedSourceFile = Table.AddColumn(RenamedPrice, "source_file", each fileName, type text),

            AddedNumber = Table.AddColumn(
                AddedSourceFile,
                "invoice_number",
                each if NumberText = null then null else "№" & Text.Trim(NumberText),
                type nullable text
            ),

            AddedDate = Table.AddColumn(AddedNumber, "invoice_date", each DocumentDate, type nullable date),

            ReorderedColumns = Table.ReorderColumns(
                AddedDate,
                {
                    "source_file",
                    "invoice_number",
                    "invoice_date",
                    "product_description",
                    "length_km",
                    "unit_price_excl_vat",
                    "comment"
                }
            )
        in
            ReorderedColumns,

    Source = try Folder.Files(DataRoot) otherwise EmptySource,

    VisibleFiles = Table.SelectRows(Source, each [Attributes]?[Hidden]? <> true),

    OnlyPdf = Table.SelectRows(
        VisibleFiles,
        each [Extension] <> null
            and Text.Lower([Extension]) = ".pdf"
            and [Folder Path] = TargetFolder
    ),

    Result =
        if Table.IsEmpty(OnlyPdf) then
            EmptyResult
        else
            let
                AddedData = Table.AddColumn(
                    OnlyPdf,
                    "Data",
                    each try ProcessPdfFile([Content], [Name]) otherwise EmptyResult,
                    type table
                ),

                DataTables = List.Select(AddedData[Data], each not Table.IsEmpty(_)),

                CombinedFiles = if List.IsEmpty(DataTables) then EmptyResult else Table.Combine(DataTables),

                FinalTypes = Table.TransformColumnTypes(
                    CombinedFiles,
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

                FixedKlMojibake1 = Table.ReplaceValue(FinalTypes, "Р С”Р В»5690", "Р С”Р В»5 690", Replacer.ReplaceText, {"product_description"}),

                FixedKlMojibake2 = Table.ReplaceValue(FixedKlMojibake1, "РєР»5690", "РєР»5 690", Replacer.ReplaceText, {"product_description"}),

                FixedKlLatin = Table.ReplaceValue(FixedKlMojibake2, "kl5690", "kl5 690", Replacer.ReplaceText, {"product_description"}),

                FixedKlCyrillic = Table.ReplaceValue(FixedKlLatin, "кл5690", "кл5 690", Replacer.ReplaceText, {"product_description"})
            in
                FixedKlCyrillic,
    #"Gefilterte Zeilen" = Table.SelectRows(Result, each not Text.StartsWith([product_description], "МК") or not Text.StartsWith([product_description], "MK"))
in
    #"Gefilterte Zeilen"