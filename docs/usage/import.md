Firstly you need to create a python module for your hardware module.

??? example "Existing SystemVerilog Module"

    ```sv title="`top.sv`"
    --8<-- "tests/testdata/importer/top.sv"
    ```
???+ example "Python Module"

    ```python
    import ucdp as u
    import ucdpsv as usv

    class TopMod(u.AMod):

        filelists: u.ClassVar[u.ModFileLists] = (u.ModFileList(name="hdl", filepaths=("top.sv",)),)

        def _build(self) -> None:
            usv.import_params_ports(self)
    ```
