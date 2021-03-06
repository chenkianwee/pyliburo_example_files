import os
import time
from py4design import py3dmodel, buildingformeval
#==============================================================================
time1 = time.perf_counter()
flr2flr = 3.7 #m
#make the floor plate
pyptlist = [[4,4,0], [-4,4,0], [-4,-4,0], [4,-4,0]]
floor_plate = py3dmodel.construct.make_polygon(pyptlist)
extrude = py3dmodel.construct.extrude(floor_plate, [0,0,1],flr2flr)
face_list = py3dmodel.fetch.topo_explorer(extrude, "face")

win_wall1 = (0.0,1.0,0.0)
win_wall2 = (0.0,-1.0,0.0)

#get the external facing walls
shade_occface_list = []
roof_occface_list = []
ext_list = []
for f in face_list:
    n = py3dmodel.calculate.face_normal(f)
    if n == win_wall1 or n == win_wall2:
        ext_list.append(f)
        
    elif n == (0.0, 0.0, 1.0):
        roof_occface_list.append(f)
    else:
        shade_occface_list.append(f)
        
#construct the windows
cut_wall_list = []
win_list = []

win1 = py3dmodel.construct.make_rectangle(1.5, 4)
win1 = py3dmodel.modify.reverse_face(win1)
mpt_win1 = py3dmodel.calculate.face_midpt(win1)
n_win1 = py3dmodel.calculate.face_normal(win1)

win2 = py3dmodel.construct.make_rectangle(2, 1.5)
win2 = py3dmodel.modify.reverse_face(win2)
mpt_win2 = py3dmodel.calculate.face_midpt(win2)
n_win2 = py3dmodel.calculate.face_normal(win2)

moved_pt1 = py3dmodel.modify.move_pt(mpt_win2, (0,1,0), 2.5 )
moved_pt2 = py3dmodel.modify.move_pt(mpt_win2, (0,-1,0), 2.5 )
win3 = py3dmodel.modify.move(mpt_win2, moved_pt1, win2)
win4 = py3dmodel.modify.move(mpt_win2, moved_pt2, win2)
cmpd = py3dmodel.construct.make_compound([win2,win3,win4])

n_win2 = py3dmodel.calculate.face_normal(win2)

for ext in ext_list:
    n = py3dmodel.calculate.face_normal(ext)
    mpt = py3dmodel.calculate.face_midpt(ext)
    ax1 = py3dmodel.construct.make_gp_ax3(mpt, n)
    if n == win_wall1:
        #create the windows
        ax2 = py3dmodel.construct.make_gp_ax3(mpt_win1, n_win1)
        mapped_win1 = py3dmodel.modify.map_cs(ax1, ax2, win1)
        mapped_win1 = py3dmodel.fetch.topo2topotype(mapped_win1)
        cut_wall = py3dmodel.construct.boolean_difference(ext, mapped_win1)
        meshed_wall = py3dmodel.construct.simple_mesh(cut_wall)
        cut_wall_list.extend(meshed_wall)
        win_list.append(mapped_win1)
        #create the corridor 
        ext_corr = py3dmodel.construct.extrude(ext, n, 1.5)
        corrs = py3dmodel.fetch.topo_explorer(ext_corr, "face")
        for cor in corrs:
            c_n = py3dmodel.calculate.face_normal(cor)
            if c_n == (0,0,1):
                shade_occface_list.append(cor)
            elif c_n == (0,0,-1):
                shade_occface_list.append(cor)
                ext_par = py3dmodel.construct.extrude(cor, (0,0,1), 1.2)
                pars = py3dmodel.fetch.topo_explorer(ext_par, "face")
                for par in pars:
                    p_n = py3dmodel.calculate.face_normal(par)
                    if p_n == (1.0, 0.0,0.0):
                        shade_occface_list.append(par)
        
    elif n == win_wall2:
        ax2 = py3dmodel.construct.make_gp_ax3(mpt_win2, n_win2)
        mapped_win2 = py3dmodel.modify.map_cs(ax1, ax2, cmpd)        
        cut_wall = py3dmodel.construct.boolean_difference(ext, mapped_win2)
        meshed_wall = py3dmodel.construct.simple_mesh(cut_wall)
        cut_wall_list.extend(meshed_wall)
        
        mapped_win2 = py3dmodel.fetch.topo_explorer(mapped_win2, "face")
        win_list.extend(mapped_win2)
        #create shade for each window
        for w in mapped_win2:
            w_n = py3dmodel.calculate.face_normal(w)
            ext_win = py3dmodel.construct.extrude(w, w_n, 1)
            shades = py3dmodel.fetch.topo_explorer(ext_win, "face")
            for shade in shades:
                s_n = py3dmodel.calculate.face_normal(shade)
                if s_n == (0,0,1):
                    shade_occface_list.append(shade)
                    

time2 = time.perf_counter()
# print("CONSTRUCTED MODEL", (time2-time1)/60.0, "mins")
# py3dmodel.utility.visualise([cut_wall_list, win_list, shade_occface_list, roof_occface_list], ["WHITE", "BLUE", "WHITE", "WHITE"])      
  
print("CALCULATING LOADS...")

#calculate ettv 
current_path = os.path.dirname(__file__)
parent_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
weatherfilepath = os.path.join(parent_path, "example_files", "weatherfile", "SGP_Singapore.486980_IWEC.epw" )
shp_attribs_list = []

for wall in cut_wall_list:
    shp_attribs = buildingformeval.create_opaque_srf_shape_attribute(wall,2.9,"wall" )
    shp_attribs_list.append(shp_attribs)

win_area = 0
for window in win_list:
    area = py3dmodel.calculate.face_area(window)
    win_area = win_area + area
    shp_attribs = buildingformeval.create_glazing_shape_attribute(window, 2.8, 0.8,"window")
    shp_attribs_list.append(shp_attribs)

for shade in shade_occface_list:
    shp_attribs = buildingformeval.create_shading_srf_shape_attribute(shade, "shade")
    shp_attribs_list.append(shp_attribs)
    
for footprint in [floor_plate]:
    shp_attribs = buildingformeval.create_shading_srf_shape_attribute(footprint, "footprint")
    shp_attribs_list.append(shp_attribs)
    
for roof in roof_occface_list:
    shp_attribs = buildingformeval.create_opaque_srf_shape_attribute(roof,0.5,"roof" )
    shp_attribs_list.append(shp_attribs)
    
#calculate sensible load
#result_dictionary = buildingformeval.calc_ettv(shp_attribs_list,weatherfilepath)
#ettv = result_dictionary["ettv"]
#facade_area = result_dictionary["facade_area"]

outdoor_temp = 32.8 #C
dewpoint = 26.3 #C
indoor_temp = 25.0 #C
occ_sens_load = 115.0 #W/person
occ_lat_load = 50.0 #W/person
equip_load = 5.0 #W/m2
lighting_load = 15.0 #W/m2
ppl_density = 2.0 #m2/person
shgc = 0.7 #solar heat gain coefficient
ceiling_height = 3.5

floor_area = py3dmodel.calculate.face_area(floor_plate)
#calculate sensible load for air-tight env
latent_load1 = buildingformeval.calc_latent_load(floor_area, 
                                                 area_per_person = ppl_density, 
                                                 watts_per_person = occ_lat_load)

equip_lighting_load = buildingformeval.calc_sensible_load(0, 0, floor_area, 
                                                          0, 0, 
                                                          equip_load_per_area = equip_load, 
                                                          occ_load_per_person = occ_sens_load, 
                                                          light_load_per_area = lighting_load, 
                                                          area_per_person = ppl_density)

env_load = buildingformeval.cal_envelope_conductance_load(shp_attribs_list, outdoor_temp, indoor_temp)

#need to calculate the solar gain from window
solar_gain_nat = buildingformeval.calc_solar_gain_rad(shp_attribs_list, weatherfilepath, mode = "max")
solar_gain_cond = solar_gain_nat * shgc
sensible_load1 = env_load + equip_lighting_load + solar_gain_cond
plenum_height = buildingformeval.calc_mech_space(sensible_load1+latent_load1, 
                                                 indoor_temp, outdoor_temp, 
                                                 duct_air_vel = 15)

print("PLENUM", plenum_height)
system_d1 = buildingformeval.central_all_air_system(sensible_load1,latent_load1, 
                                                    floor_area, 
                                                    supply_temp_c = 8.0, 
                                                    rej_temp_c = outdoor_temp,
                                                    chiller_efficiency = 0.4)

system_d2 = buildingformeval.central_all_air_system(sensible_load1, latent_load1, 
                                                    floor_area, 
                                                    supply_temp_c = 8.0, 
                                                    rej_temp_c = outdoor_temp,
                                                    chiller_efficiency = 0.6)

#calculate sensible load for condensation free panels
sensible_load2 = buildingformeval.calc_sensible_load(0, 0, floor_area, 0, 0,  
                                                     equip_load_per_area = 0.0, 
                                                     occ_load_per_person = occ_sens_load, 
                                                     light_load_per_area = 0.0, 
                                                     area_per_person = ppl_density)
ach_list = [50]
for ach in ach_list:
    #calculate sensible load for natural ventilation
    ach_dict = buildingformeval.calc_ach_4_equip(floor_area, flr2flr, equip_load, 
                                                 lighting_load, solar_gain_nat, 
                                                 ['air_velocity', win_area],
                                                 mx_ach = ach,
                                                 air_temp_c = outdoor_temp)
    
    temp_increase = ach_dict['temp_increase']
    mem_air_temp = outdoor_temp + temp_increase
    
    system_d3 = buildingformeval.con_free_panels_w_fans(sensible_load2, floor_area, 
                                                        out_temp_c = outdoor_temp, 
                                                        interior_temp_c = mem_air_temp, 
                                                        dewpt_temp_c = dewpoint, 
                                                        m2_per_fan= 15, fan_power = 75, 
                                                        percent_ceiling = 0.73, 
                                                        chiller_efficiency = 0.4)
    
    system_d4 = buildingformeval.con_free_panels_w_fans(sensible_load2, floor_area, 
                                                        out_temp_c = outdoor_temp, 
                                                        interior_temp_c = mem_air_temp, 
                                                        dewpt_temp_c = dewpoint, 
                                                        m2_per_fan= 15, fan_power = 75, 
                                                        percent_ceiling = 0.73, 
                                                        chiller_efficiency = 0.6)
    
    print("*******************************************************************")
    # print("ACH PARAMETERS", ach_dict)
    # print('Temp increase', temp_increase)
    # print("Interior Air Temp", mem_air_temp)
    # print("SOLAR GAIN", solar_gain_nat)
    
    print("LATENT LOAD", latent_load1)
    print("SENSIBLE LOAD FOR AIR-BASED", sensible_load1, "SENSIBLE LOAD FOR RADIANT-BASED", sensible_load2)
    print("*******************************************************************")
    print("DECENTRALISED ALL-AIR-ENERGY", system_d1["energy_consumed_hr"], "COP =",  system_d1["overall_cop"])
    print("*******************************************************************")
    print("CENTRALISED ALL-AIR-ENERGY", system_d2["energy_consumed_hr"], "COP =",  system_d2["overall_cop"])
    print("*******************************************************************")
    print("DECENTRALISED CONDENSATION-FREE-ENERGY=", system_d3["energy_consumed_hr"], "COP =",  system_d3["sensible_cop"] ,"PANEL SUPPLY TEMP=", system_d3["supply_temperature_for_panels"] - 273.15)
    print("*******************************************************************")
    print("CENTRALISED CONDENSATION-FREE-ENERGY=", system_d4["energy_consumed_hr"], "COP =",  system_d4["sensible_cop"] ,"PANEL SUPPLY TEMP=", system_d4["supply_temperature_for_panels"] - 273.15)
    print('Energy Demand', round(system_d4["energy_consumed_hr"]),'W',
          '\nPANEL CAPACITY', system_d4['panel_capacity'],
          '\nFAN CAPACITY', system_d4['fan_capacity'],
          '\nEVA CAPACITY', system_d4['eva_capacity'],
          "\nPANEL SUPPLY TEMP =", system_d4["supply_temperature_for_panels"] - 273.15)
    
    #print "HOW MANY TIMES LOWER", system_d1["energy_consumed_hr"]/ system_d2 ["energy_consumed_hr"]
    print("*******************************************************************")