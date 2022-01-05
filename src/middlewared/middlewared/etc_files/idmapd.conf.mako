<%
    config = middleware.call_sync("nfs.config")
    if not config["v4"]:
        raise FileShouldNotExist()
%>

[General]
Verbosity = 0

[Mapping]
Nobody-User = nobody
Nobody-Group = nogroup

[Translation]
Method = nsswitch