let
    Quelle = (Parameter3) => let
        Quelle = Excel.Workbook(Parameter3, null, true),
        Лист1_Sheet = Quelle{[Item="Лист1",Kind="Sheet"]}[Data],
        #"Höher gestufte Header" = Table.PromoteHeaders(Лист1_Sheet, [PromoteAllScalars=true])
    in
        #"Höher gestufte Header"
in
    Quelle