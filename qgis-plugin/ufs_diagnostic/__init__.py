def classFactory(iface):
    from .ufs_diagnostic import UfsDiagnosticPlugin
    return UfsDiagnosticPlugin(iface)
