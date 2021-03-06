import os
import time
from py4design import pycitygml, py3dmodel

#================================================================================
#INSTRUCTION: SPECIFY THE CITYGML FILE
#================================================================================
#specify the citygml file
current_path = os.path.dirname(__file__)
parent_path = parent_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
citygml_filepath = os.path.join(parent_path, "example_files", "citygml", "punggol.gml" )
#or just insert a citygml file you would like to analyse here 
'''citygml_filepath = "C://file2analyse.gml"'''
#================================================================================
#INSTRUCTION: SPECIFY THE CITYGML FILE
#================================================================================
time1 = time.clock()
display_2dlist = []
colour_list = []
#===================================================================================================
#read the citygml file 
#===================================================================================================
citygml_list = [citygml_filepath]
road_occedges = []
stations = []
ldisplay_list = []
edgedisplay_list = []
bdisplay_list = []
rdisplay_list = []

for citygml_filepath in citygml_list:
    read_citygml = pycitygml.Reader()
    read_citygml.load_filepath(citygml_filepath)
    buildings = read_citygml.get_buildings()
    landuses = read_citygml.get_landuses()
    stops = read_citygml.get_bus_stops()
    roads = read_citygml.get_roads()
    railways = read_citygml.get_railways()
    reliefs = read_citygml.get_relief_feature()
    
    print "nbuildings:", len(buildings)
    
    #get all the polylines of the lod0 roads
    
    for road in roads:
        polylines = read_citygml.get_pylinestring_list(road)
        for polyline in polylines:
            occ_wire = py3dmodel.construct.make_wire(polyline)
            edge_list = py3dmodel.fetch.topo_explorer(occ_wire, "edge")
            road_occedges.extend(edge_list)
    
    #get all the polygons of the landuses
    for landuse in landuses:
        polygons = read_citygml.get_polygons(landuse)
        
    #get all the stations in the buildings and extract their polygons 
    
    for building in buildings:
        polygons = read_citygml.get_polygons(building)
        for polygon in polygons:
            polygon_id = polygon.attrib["{%s}id" % read_citygml.namespaces['gml']]
            pos_list = read_citygml.get_polygon_pt_list(polygon)
            
    
    #extract all the footprint of the buildings 
    bcnt = 0
    for building in buildings:
        pypolgon_list = read_citygml.get_pypolygon_list(building)
        solid = py3dmodel.construct.make_occsolid_frm_pypolygons(pypolgon_list)
        edgelist = py3dmodel.fetch.topo_explorer(solid, "edge")
        bdisplay_list.append(solid)
        edgedisplay_list.extend(edgelist)
        bcnt+=1
        
    
    
    print "NPLOTS", len(landuses)
    for landuse in landuses:
        lpolygons = read_citygml.get_polygons(landuse)
        if lpolygons:
            for lpolygon in lpolygons:
                landuse_pts = read_citygml.polygon_2_pyptlist(lpolygon)
                lface = py3dmodel.construct.make_polygon(landuse_pts)
                fedgelist = py3dmodel.fetch.topo_explorer(lface, "edge")
                edgedisplay_list.extend(fedgelist)
                ldisplay_list.append(lface)
          
    
    for relief in reliefs:
        pytri_list = read_citygml.get_pytriangle_list(relief)
        for pytri in pytri_list:
            rface = py3dmodel.construct.make_polygon(pytri)
            rdisplay_list.append(rface)
    
time2 = time.clock()   
time = (time2-time1)/60.0
print "TIME TAKEN", time
print "VISUALISING"  


display_2dlist.append(ldisplay_list)
display_2dlist.append(bdisplay_list)
display_2dlist.append(rdisplay_list)
display_2dlist.append(edgedisplay_list)
display_2dlist.append(road_occedges)
colour_list.append('WHITE')
colour_list.append('WHITE')
colour_list.append('WHITE')
colour_list.append('BLACK')
colour_list.append('BLACK')
py3dmodel.utility.visualise(display_2dlist, colour_list)
