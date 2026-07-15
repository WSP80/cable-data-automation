let
    Quelle = Csv.Document(Parameter4,[Delimiter=";", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Höher gestufte Header" = Table.PromoteHeaders(Quelle, [PromoteAllScalars=true])
in
    #"Höher gestufte Header"