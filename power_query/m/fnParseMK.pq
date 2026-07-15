(FileBinary as binary, FileName as text) as table =>
let
    Quelle = Pdf.Tables(FileBinary),

    Tabellen = Table.SelectRows(
        Quelle,
        each Text.StartsWith([Name], "Table")
    ),

    MitSort = Table.AddColumn(
        Tabellen,
        "Sort",
        each try Number.FromText(Text.Select(Text.BeforeDelimiter([Name], " "), {"0".."9"})) otherwise 999999,
        Int64.Type
    ),

    Sortiert = Table.Sort(MitSort, {{"Sort", Order.Ascending}}),

    TabellenListe = Sortiert[Data],

    LeerTabelle =
        #table(
            {
                "Номер КП",
                "Дата КП",
                "Наименование продукции",
                "Количество",
                "Цена без учета#(lf)НДС, руб",
                "Комментарий"
            },
            {}
        ),

    Ergebnis =
        if List.Count(TabellenListe) = 0 then
            LeerTabelle
        else
            let
                ErsteTabelleRaw = TabellenListe{0},
                AndereTabellenRaw = List.Skip(TabellenListe, 1),

                fnErsteTabelle = (t as table) as table =>
                    let
                        Promote = Table.PromoteHeaders(t, [PromoteAllScalars = true]),
                        Auswahl = Table.SelectColumns(
                            Promote,
                            {
                                "Наименование продукции",
                                "Количество",
                                "Цена без учета#(lf)НДС, руб",
                                "Примечание"
                            },
                            MissingField.UseNull
                        ),
                        Umbenannt = Table.RenameColumns(
                            Auswahl,
                            {{"Примечание", "Комментарий"}},
                            MissingField.Ignore
                        )
                    in
                        Umbenannt,

                fnAndereTabelle = (t as table) as table =>
                    let
                        ColNames = Table.ColumnNames(t),

                        ErgebnisAndere =
                            if List.Count(ColNames) >= 6 then
                                let
                                    Auswahl = Table.SelectColumns(
                                        t,
                                        {ColNames{1}, ColNames{2}, ColNames{4}, ColNames{5}},
                                        MissingField.UseNull
                                    ),
                                    Umbenannt = Table.RenameColumns(
                                        Auswahl,
                                        {
                                            {ColNames{1}, "Наименование продукции"},
                                            {ColNames{2}, "Количество"},
                                            {ColNames{4}, "Цена без учета#(lf)НДС, руб"},
                                            {ColNames{5}, "Комментарий"}
                                        },
                                        MissingField.Ignore
                                    )
                                in
                                    Umbenannt
                            else if List.Count(ColNames) >= 5 then
                                let
                                    Auswahl = Table.SelectColumns(
                                        t,
                                        {ColNames{1}, ColNames{2}, ColNames{4}},
                                        MissingField.UseNull
                                    ),
                                    Umbenannt = Table.RenameColumns(
                                        Auswahl,
                                        {
                                            {ColNames{1}, "Наименование продукции"},
                                            {ColNames{2}, "Количество"},
                                            {ColNames{4}, "Цена без учета#(lf)НДС, руб"}
                                        },
                                        MissingField.Ignore
                                    ),
                                    MitKommentar = Table.AddColumn(
                                        Umbenannt,
                                        "Комментарий",
                                        each null,
                                        type text
                                    )
                                in
                                    MitKommentar
                            else
                                #table(
                                    {
                                        "Наименование продукции",
                                        "Количество",
                                        "Цена без учета#(lf)НДС, руб",
                                        "Комментарий"
                                    },
                                    {}
                                )
                    in
                        ErgebnisAndere,

                ErsteTabelle = fnErsteTabelle(ErsteTabelleRaw),

                AndereTabellen =
                    List.Transform(
                        AndereTabellenRaw,
                        each fnAndereTabelle(_)
                    ),

                Kombiniert =
                    Table.Combine(
                        List.Combine(
                            {
                                {ErsteTabelle},
                                AndereTabellen
                            }
                        )
                    ),

                Gefiltert = Table.SelectRows(
                    Kombiniert,
                    each
                        [Наименование продукции] <> null and
                        Text.Trim(Text.From([Наименование продукции])) <> "" and
                        [Наименование продукции] <> "Итого" and
                        [Наименование продукции] <> "ИТОГО:" and
                        [Наименование продукции] <> "Наименование продукции"
                ),

                PreisOhneLeerzeichen = Table.ReplaceValue(
                    Gefiltert,
                    " ",
                    "",
                    Replacer.ReplaceText,
                    {"Цена без учета#(lf)НДС, руб"}
                ),

                Typen = Table.TransformColumnTypes(
                    PreisOhneLeerzeichen,
                    {
                        {"Наименование продукции", type text},
                        {"Количество", type number},
                        {"Цена без учета#(lf)НДС, руб", type number},
                        {"Комментарий", type text}
                    },
                    "ru-RU"
                ),

                NummerKPRaw =
                    try Text.BetweenDelimiters(FileName, "№ ", " от")
                    otherwise null,

                NummerKP =
                    if NummerKPRaw = null then
                        null
                    else if Text.StartsWith(NummerKPRaw, "№") then
                        NummerKPRaw
                    else
                        "№" & NummerKPRaw,

                DatumKPText =
                    try Text.BeforeDelimiter(Text.AfterDelimiter(FileName, " от "), ".pdf")
                    otherwise try Text.AfterDelimiter(FileName, " от ")
                    otherwise null,

                DatumKP =
                    try Date.FromText(DatumKPText, [Format = "dd.MM.yyyy"])
                    otherwise null,

                MitNummer = Table.AddColumn(
                    Typen,
                    "Номер КП",
                    each NummerKP,
                    type text
                ),

                MitDatum = Table.AddColumn(
                    MitNummer,
                    "Дата КП",
                    each DatumKP,
                    type date
                ),

                Reihenfolge = Table.ReorderColumns(
                    MitDatum,
                    {
                        "Номер КП",
                        "Дата КП",
                        "Наименование продукции",
                        "Количество",
                        "Цена без учета#(lf)НДС, руб",
                        "Комментарий"
                    },
                    MissingField.Ignore
                )
            in
                Reihenfolge
in
    Ergebnis