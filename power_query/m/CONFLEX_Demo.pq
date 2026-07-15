let
    DataRoot = "D:\Weiterbildung\6.PortfolioProject\data",
    TargetFolder = "D:\Weiterbildung\6.PortfolioProject\data\demo\raw\",
    ManufacturerCode = "CONFLEX",

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

    ToNumber = (value as nullable any) as nullable number =>
        let
            TextValue =
                if value = null then
                    null
                else
                    Text.Trim(Text.From(value)),

            CleanValue =
                if TextValue = null then
                    null
                else
                    Text.Replace(
                        Text.Replace(TextValue, Character.FromNumber(160), ""),
                        " ",
                        ""
                    ),

            Result =
                try Number.FromText(CleanValue, "ru-RU") otherwise null
        in
            Result,

    TransformDemoCsv = (fileContent as binary, fileName as text) as table =>
        let
            RawCsv =
                Csv.Document(
                    fileContent,
                    [
                        Delimiter = ";",
                        Columns = 4,
                        Encoding = 65001,
                        QuoteStyle = QuoteStyle.Csv
                    ]
                ),

            DataRows =
                if Table.IsEmpty(RawCsv) then
                    RawCsv
                else
                    Table.Skip(RawCsv, 1),

            RenamedColumns =
                Table.RenameColumns(
                    DataRows,
                    {
                        {"Column1", "invoice_date_raw"},
                        {"Column2", "product_description"},
                        {"Column3", "unit_price_raw"},
                        {"Column4", "extra_column"}
                    },
                    MissingField.Ignore
                ),

            AddedSourceFile =
                Table.AddColumn(
                    RenamedColumns,
                    "source_file",
                    each fileName,
                    type text
                ),

            AddedInvoiceNumber =
                Table.AddColumn(
                    AddedSourceFile,
                    "invoice_number",
                    each null,
                    type nullable text
                ),

            AddedInvoiceDate =
                Table.AddColumn(
                    AddedInvoiceNumber,
                    "invoice_date",
                    each try Date.FromText(Text.From([invoice_date_raw]), "ru-RU") otherwise null,
                    type nullable date
                ),

            AddedLength =
                Table.AddColumn(
                    AddedInvoiceDate,
                    "length_km",
                    each null,
                    type nullable number
                ),

            AddedUnitPrice =
                Table.AddColumn(
                    AddedLength,
                    "unit_price_excl_vat",
                    each ToNumber([unit_price_raw]),
                    type nullable number
                ),

            AddedComment =
                Table.AddColumn(
                    AddedUnitPrice,
                    "comment",
                    each null,
                    type nullable text
                ),

            SelectedColumns =
                Table.SelectColumns(
                    AddedComment,
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

            CleanedText =
                Table.TransformColumns(
                    SelectedColumns,
                    {
                        {
                            "product_description",
                            each if _ = null then null else Text.Trim(Text.Clean(Text.From(_))),
                            type text
                        }
                    }
                ),

            FixedKlLatin =
                Table.ReplaceValue(
                    CleanedText,
                    "kl5690",
                    "kl5 690",
                    Replacer.ReplaceText,
                    {"product_description"}
                ),

            FixedKlCyrillic =
                Table.ReplaceValue(
                    FixedKlLatin,
                    "кл5690",
                    "кл5 690",
                    Replacer.ReplaceText,
                    {"product_description"}
                ),

            FixedKlMojibake =
                Table.ReplaceValue(
                    FixedKlCyrillic,
                    "РєР»5690",
                    "РєР»5 690",
                    Replacer.ReplaceText,
                    {"product_description"}
                ),

            FilteredRows =
                Table.SelectRows(
                    FixedKlMojibake,
                    each [product_description] <> null
                        and [product_description] <> ""
                        and [unit_price_excl_vat] <> null
                )
        in
            FilteredRows,

    Quelle =
        try Folder.Files(DataRoot) otherwise EmptySource,

    VisibleFiles =
        Table.SelectRows(
            Quelle,
            each [Attributes]?[Hidden]? <> true
        ),

    CsvFiles =
        Table.SelectRows(
            VisibleFiles,
            each [Extension] <> null
                and Text.Lower([Extension]) = ".csv"
                and [Folder Path] = TargetFolder
                and Text.Contains([Name], ManufacturerCode)
        ),

    Result =
        if Table.IsEmpty(CsvFiles) then
            EmptyResult
        else
            let
                AddedData =
                    Table.AddColumn(
                        CsvFiles,
                        "Data",
                        each try TransformDemoCsv([Content], [Name]) otherwise EmptyResult,
                        type table
                    ),

                DataTables =
                    List.Select(
                        AddedData[Data],
                        each not Table.IsEmpty(_)
                    ),

                CombinedFiles =
                    if List.IsEmpty(DataTables) then
                        EmptyResult
                    else
                        Table.Combine(DataTables),

                FinalTypes =
                    Table.TransformColumnTypes(
                        CombinedFiles,
                        {
                            {"source_file", type text},
                            {"invoice_number", type text},
                            {"invoice_date", type date},
                            {"product_description", type text},
                            {"length_km", type number},
                            {"unit_price_excl_vat", type number},
                            {"comment", type text}
                        }
                    )
            in
                FinalTypes
in
    Result