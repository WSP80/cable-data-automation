let
    Quelle = (Parameter5) => let
        Quelle = Csv.Document(Parameter5,[Delimiter=";", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
        #"Höher gestufte Header" = Table.PromoteHeaders(Quelle, [PromoteAllScalars=true])
    in
        #"Höher gestufte Header"
in
    Quelle