# Version-specific guard for the installed SNOWPACK 3.7.0 build.
# Stop immediately after compSurfaceSublimation, which can remove the last layer.
# At LayerToLayer + 61 bytes no temporary vectors have been allocated yet.
set pagination off
set confirm off
set debuginfod enabled off
set $empty_column_guards = 0
start
break *(_ZN15VapourTransport12LayerToLayerERK12CurrentMeteoR11SnowStationR13SurfaceFluxesRd + 61) if Xdata.nElems == 0
commands
    silent
    set $empty_column_guards = $empty_column_guards + 1
    return
    continue
end
continue
printf "[numerics] Empty-column LayerToLayer guards: %d\n", $empty_column_guards
