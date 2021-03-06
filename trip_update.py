import psycopg2
import ast
import numpy as np
import simplejson
import urllib
import json
import re
from helpers import *
import os

current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]

def convert_event_ids_to_lst(event_ids):
    try:
        if type(ast.literal_eval(event_ids)) == list:
            new_event_ids = map(int,ast.literal_eval(event_ids))
        else: 
            event_ids = re.sub("\s+", ",", event_ids.strip())
            event_ids = event_ids.replace('.','')
            new_event_ids = map(int,event_ids.strip('[').strip(']').strip(',').split(','))
    except:
        event_ids = re.sub("\s+", " ", event_ids.replace('[','').replace(']','').strip()).split(' ')
        new_event_ids = map(int,map(float,event_ids))
    return new_event_ids

# def add_search_event(poi_name, trip_location_id):
#     '''
#     input: name from poi_detail_table; trip_location_id from day_trip_table
#     output: 7 items of items.
#     '''
#     conn = psycopg2.connect(conn_str)
#     cur = conn.cursor()
#     cur.execute("SELECT county, state, event_ids FROM day_trip_table_city WHERE trip_locations_id  = '%s' LIMIT 1;" %(trip_location_id))  
#     county, state, event_ids = cur.fetchone()
#     event_ids = convert_event_ids_to_lst(event_ids)
#     new_event_ids = tuple(event_ids)
#     cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND county='{1}' AND state='{2}' and name % '{3}' ORDER BY similarity(name, '{3}') DESC LIMIT 7;".format(new_event_ids, county.upper(),state.title(), poi_name))
#     # print "SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND county='{1}' AND state='{2}' and name % '{3}' ORDER BY similarity(name, '{3}') DESC LIMIT 7;".format(new_event_ids, county,state, poi_name)
#     results = cur.fetchall()
#     poi_ids, poi_lst = [int(row[0]) for row in results], [row[1] for row in results]
#     # poi_ids = convert_event_ids_to_lst(poi_ids)
#     print 'add search result: ', poi_ids, poi_lst
#     if 7-len(poi_lst)>0:
#         event_ids.extend(poi_ids)
#         event_ids = str(tuple(event_ids))
#         cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND county='{1}' AND state='{2}' ORDER BY num_reviews DESC LIMIT {3};".format(event_ids, county.upper(), state.title(), 7-len(poi_lst)))
#         results.extend(cur.fetchall())
#     poi_dict = {d[1]:d[0] for d in results}
#     poi_names = [d[1] for d in results]
#     conn.close()
#     return poi_dict, poi_names

def suggest_search_pop_events(trip_location_id):
    '''
    input: trip_location_id from day_trip_table
    output: 7 items of items.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT city, state, event_ids FROM day_trip_table_city WHERE trip_locations_id  = '%s' LIMIT 1;" %(trip_location_id))  
    city, state, event_ids = cur.fetchone()
    event_ids = json.loads(event_ids)
    cur.execute("SELECT index, name, address, adjusted_visit_length, city, state, coord_lat, coord_long, poi_type, img_url FROM poi_detail_table WHERE index NOT IN %s AND city=%s AND state=%s ORDER BY num_reviews DESC LIMIT 7;", (tuple(event_ids), city.title(), state.title()))
    results = cur.fetchall()
    poi_dict_list = []
    for index, name, address, adjusted_visit_length, city, state, coord_lat, coord_long, poi_type, img_url in results:
        poi_dict = {'event_id': index,
                    'name': name,
                    'address': address,
                    'adjusted_visit_length': adjusted_visit_length,
                    'city': city,
                    'state': state,
                    'coord_lat': coord_lat,
                    'coord_long': coord_long,
                    'poi_type': poi_type,
                    'img_url': img_url
                    }
        poi_dict_list.append(poi_dict)
    conn.close()
    return poi_dict_list


def add_search_event(poi_name, trip_location_id):
    '''
    input: name from poi_detail_table; trip_location_id from day_trip_table
    output: 7 items of items.
    '''

    '''
    need to chnage to radius
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT city, state, event_ids FROM day_trip_table_city WHERE trip_locations_id  = '%s' LIMIT 1;" %(trip_location_id))  
    city, state, event_ids = cur.fetchone()
    # print event_ids, type(event_ids)
    event_ids = json.loads(event_ids)
    # print event_ids, type(event_ids)
    event_ids = map(int, event_ids)
    new_event_ids = tuple(event_ids)

    # print new_event_ids, type(new_event_ids)
    cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND city='{1}' AND state='{2}' and name % '{3}' ORDER BY similarity(name, '{3}') DESC LIMIT 7;".format(new_event_ids, city.title(),state.title(), poi_name))
    # print "SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND county='{1}' AND state='{2}' and name % '{3}' ORDER BY similarity(name, '{3}') DESC LIMIT 7;".format(new_event_ids, county,state, poi_name)
    results = cur.fetchall()
    poi_ids, poi_lst = [int(row[0]) for row in results], [row[1] for row in results]
    # poi_ids = convert_event_ids_to_lst(poi_ids)
    print 'add search result: ', poi_ids, poi_lst
    if 7-len(poi_lst)>0:
        event_ids.extend(poi_ids)
        event_ids = str(tuple(event_ids))
        cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND city='{1}' AND state='{2}' ORDER BY num_reviews DESC LIMIT {3};".format(event_ids, city.title(), state.title(), 7-len(poi_lst)))
        results.extend(cur.fetchall())
    poi_dict = {d[1]:d[0] for d in results}
    poi_names = [d[1] for d in results]
    conn.close()
    return poi_dict, poi_names

def outside_add_search_event(poi_name, outside_route_id):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT origin_city, origin_state, event_ids FROM outside_route_table WHERE outside_route_id =  '%s' LIMIT 1;" %(outside_route_id))
    city, state, event_ids = cur.fetchone()

    event_ids = map(int,map(float,event_ids.replace("[","").replace("]","").replace(" ","").split(",")))


    new_event_ids = tuple(event_ids)
    cur.execute("SELECT index, coord_lat, coord_long FROM all_cities_coords_table WHERE city ='%s' AND state = '%s';" % (city, state))
    id_, start_lat, start_long = cur.fetchone()
    cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND interesting = True AND ST_Distance_Sphere(geom, ST_MakePoint({2},{3})) <= 150 * 1609.34 and name % '{1}'  ORDER BY similarity(name, '{1}') DESC LIMIT 7;".format(new_event_ids, poi_name, start_long, start_lat))

    results = cur.fetchall()
    if results > 0:
        poi_ids, poi_lst = [int(row[0]) for row in results], [row[1] for row in results]
    else:
        poi_ids, poi_lst = [], []
        
    if 7-len(poi_lst)>0:
        event_ids.extend(poi_ids)
        new_event_ids = str(tuple(event_ids))
        cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND interesting = True AND ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 150 * 1609.34 ORDER BY num_reviews DESC LIMIT {3};".format(new_event_ids, start_long, start_lat, 7-len(poi_ids)))

        results.extend(cur.fetchall())
    poi_dict = {d[1]:d[0] for d in results}
    poi_names = [d[1] for d in results]
    conn.close()

    return poi_dict, poi_names



def add_event_day_trip(poi_id, poi_name, trip_locations_id, full_trip_id, full_day = True, unseen_event = False, username_id=1):
    '''
    Future feature: day number is sth to remind! need to create better details maybe
    '''
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()
    username_id = 1   
    cur.execute("select full_day, event_ids, details from day_trip_table_city where trip_locations_id='%s'" %(trip_locations_id))  
    (full_day, event_ids, day_details) = cur.fetchone()
    cur.execute("select trip_location_ids, details, city, state, n_days from full_trip_table_city where full_trip_id='%s'" %(full_trip_id))  
    (trip_location_ids, full_trip_details, city, state, n_days) = cur.fetchone()
    event_ids = json.loads(event_ids)
    event_ids = map(int, event_ids)
    day_details = json.loads(day_details)
    if not poi_id:
        new_trip_location_id = '-'.join(map(str,event_ids))+'-'+str(poi_name).replace(' ','-').replace("'",'')
        cur.execute("select details from day_trip_table_city where trip_locations_id=%s",(new_trip_location_id,))
        a = cur.fetchone()
        if bool(a):
            conn.close()
            details = json.loads(a[0])
            return trip_locations_id, new_trip_location_id, details
        else:
            cur.execute("select max(index) from day_trip_table_city;")
            new_index = cur.fetchone()[0]+1
            day = day_details[-1]['day']
            new_event_detail = {"name": poi_name, "day": day, "coord_lat": "None", "coord_long": "None","address": "None", "id": "None", "city": "", "state": ""}
            day_details.append(new_event_detail)
            event_ids.append(poi_name)
            cur.execute("INSERT INTO day_trip_table_city VALUES (%i, '%s',%s,%s,'%s','%s','%s','%s','%s');" %(new_index, new_trip_location_id, full_day, False, city, state, json.dumps(day_detail),'add',json.dumps(event_ids)))
            conn.commit()
            conn.close()
            return trip_locations_id, new_trip_location_id, day_detail
    else:
        event_ids, event_type = db_event_cloest_distance(trip_locations_id=trip_locations_id, new_event_id=poi_id)
        event_ids=event_ids.tolist()
        event_ids, driving_time_list, walking_time_list = db_google_driving_walking_time(event_ids,event_type = 'add')
        if trip_locations_id.isupper() or trip_locations_id.islower():
            new_trip_location_id = '-'.join(map(str,event_ids))+'-'+str(poi_id)
        else:
            new_trip_location_id = '-'.join(map(str,event_ids))
        cur.execute("select details from day_trip_table_city where trip_locations_id=%s", (new_trip_location_id,)) 
        a = cur.fetchone()
        if not a:
            details = []
            event_day = day_details[0]['day']
            for item in event_ids:
                cur.execute("select index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url from poi_detail_table where index = '%s';" %(item))
                a = cur.fetchone()
                detail = {'id': a[0],'name': a[1],'address': a[2], 'day': event_day, 'coord_lat': a[3], 'coord_long': a[4], 'city': a[5], 'state': a[6], 'icon_url': a[7], 'check_full_address': a[8], 'poi_type': a[9], 'adjusted_visit_length': a[10], 'img_url': a[11]}
                details.append(detail)
            cur.execute("select max(index) from day_trip_table_city;")
            new_index = cur.fetchone()[0] +1
            event_type = 'add'
            cur.execute("insert into day_trip_table_city (index, trip_locations_id,full_day, regular, city, state, details, event_type, event_ids) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" ,(new_index, new_trip_location_id, full_day, False, city, state, json.dumps(details), event_type, json.dumps(event_ids)))
            conn.commit()
            conn.close()
            return trip_locations_id, new_trip_location_id, details
        else:
            conn.close()
            details = json.loads(a[0])
            return trip_locations_id, new_trip_location_id, details

def auto_add_event_id_lst(full_trip_id,time_limit=60):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT city, state,  details FROM full_trip_table_city WHERE full_trip_id  = '%s' LIMIT 1;" %(full_trip_id))  
    city, state, details = cur.fetchone()
    details = json.loads(details)
    event_ids = [detail['id'] for detail in details]
    cur.execute("SELECT index, name, adjusted_visit_length, num_reviews FROM poi_detail_table WHERE index NOT IN {0} AND city='{1}' AND state='{2}' AND adjusted_visit_length <= 60 ORDER BY num_reviews DESC LIMIT {3};".format(str(tuple(event_ids)), city.title(), state.title(), 4))
    results = cur.fetchall()

    conn.close()
    total_time = 0
    add_poi_id_lst = []
    if len(results)==0:
        return add_poi_id_lst
    for result in results:
        total_time += int(result[2])
        add_poi_id_lst.append((result[0],result[1]))
        if total_time>=time_limit:
            return add_poi_id_lst
    return add_poi_id_lst

def auto_add_events_full_trip(trip_location_id,full_trip_id, time_limit=60):
    add_poi_id_lst = auto_add_event_id_lst(full_trip_id,time_limit)
    if len(add_poi_id_lst) != 0:
        for (poi_id,poi_name) in add_poi_id_lst:
            old_trip_location_id, trip_location_id, new_day_details = add_event_day_trip(poi_id, poi_name, trip_location_id, full_trip_id)
            full_trip_id, trip_location_ids, full_trip_details = add_event_full_trip(full_trip_id, old_trip_location_id, trip_location_id, new_day_details)
        return full_trip_id, trip_location_ids, full_trip_details, trip_location_id
    else:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("SELECT trip_location_ids,details FROM full_trip_table_city WHERE full_trip_id  = '%s' LIMIT 1;" %(full_trip_id))  
        trip_location_ids, details = cur.fetchone()
        return full_trip_id, json.loads(trip_location_ids), json.loads(details),trip_location_id
        
def add_event_route_trip(poi_id, poi_name, outside_route_id, outside_trip_id, full_day = True, unseen_event = False, username_id=1):
    #day number is sth to remind! need to create better details maybe
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()
    username_id = 1  
    cur.execute("select full_day, event_ids, details from outside_route_table where outside_route_id='%s'" %(outside_route_id))  
    (full_day, event_ids, route_details) = cur.fetchone()
    cur.execute("select outside_route_ids, details, county, state, n_days from outside_trip_table where outside_trip_id='%s'" %(outside_trip_id))  
    (outside_route_ids, outside_trip_details, county, state, n_days) = cur.fetchone()
    event_ids = json.loads(event_ids)
    route_details = json.loads(route_details)
    conn.close()

def add_event_full_trip(old_full_trip_id, old_trip_location_id, new_trip_location_id, new_day_details, username_id=1):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()
    username_id = 1   
    cur.execute("select full_day, event_ids, details from day_trip_table_city where trip_locations_id='%s'" %(new_trip_location_id))  
    (full_day, event_ids, day_details) = cur.fetchone()
    cur.execute("select trip_location_ids, city, state, n_days from full_trip_table_city where full_trip_id='%s'" %(old_full_trip_id))  
    (trip_location_ids, city, state, n_days) = cur.fetchone()
    trip_location_ids = json.loads(trip_location_ids)
    for i, v in enumerate(trip_location_ids):
        if v == old_trip_location_id: 
            idx = i
            trip_location_ids[i] = new_trip_location_id
            break
    new_full_trip_id = '-'.join(trip_location_ids)
    if not check_full_trip_id(new_full_trip_id):
        new_details = []
        for trip_location_id in trip_location_ids:
            cur.execute("select details from day_trip_table_city where trip_locations_id='%s'" %(trip_location_id))  
            details = cur.fetchone()[0]
            details = json.loads(details)
            for detail in details:
                if type(detail) == str:
                    detail = ast.literal_eval(detail)
                new_details.append(detail)
        cur.execute("SELECT max(index) from full_trip_table_city;")
        new_index = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO full_trip_table_city (index, username_id, full_trip_id,trip_location_ids, regular, city, state, details, n_days) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);" ,(new_index, username_id, new_full_trip_id, json.dumps(trip_location_ids), False, city, state, json.dumps(new_details), n_days))
        conn.commit()

    else:
        cur.execute("SELECT trip_location_ids, details FROM full_trip_table_city WHERE full_trip_id = '%s';"%(new_full_trip_id))
        trip_location_ids, new_details = cur.fetchone()
        trip_location_ids = json.loads(trip_location_ids)
        new_details = json.loads(new_details)

    conn.close()
    return new_full_trip_id, trip_location_ids, new_details

'''
Need to update db for last item delete..need to fix bugs if any
'''
def remove_event(full_trip_id, trip_locations_id, remove_event_id, username_id=1, remove_event_name=None, event_day=None, full_day = True):
    #may have some bugs if trip_locations_id != remove_event_id as last one:)   test and need to fix
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()
    if trip_locations_id == remove_event_id:
        if full_trip_id != trip_locations_id:
            # full_trip_id = full_trip_id[len(str(trip_locations_id))+1:]
            cur.execute("select trip_location_ids from full_trip_table_city where full_trip_id = '%s';" %(full_trip_id)) 
            # cur.execute("select trip_location_ids, details from full_trip_table where full_trip_id = '%s';" %(full_trip_id)) 
            trip_location_ids = cur.fetchone()[0]
            trip_location_ids = json.loads(trip_location_ids)
            trip_location_ids.remove(trip_locations_id)
            full_trip_details = []
            for trip_id in trip_location_ids:
                cur.execute("select details from day_trip_table_city where trip_locations_id = '%s';" %(trip_id)) 
                details = cur.fetchone()[0]
                trip_details = json.loads(details)
                full_trip_details.extend(trip_details)
            conn.close()
            new_full_trip_id = '-'.join(trip_location_ids)
            for index, detail in enumerate(full_trip_details):
                full_trip_details[index] = detail
                full_trip_details[index]['address'] = full_trip_details[index]['address'].strip(', ').replace(', ,',',')
            return new_full_trip_id, full_trip_details, trip_location_ids
        return '','',''
    
    cur.execute("select * from day_trip_table_city where trip_locations_id='%s'" %(trip_locations_id)) 
    (index, trip_locations_id, full_day, regular, city, state, detail, event_type, event_ids) = cur.fetchone()
    new_event_ids = json.loads(event_ids)
    remove_event_id = int(remove_event_id)
    new_event_ids.remove(remove_event_id)
    new_trip_locations_id = '-'.join(str(int(event_id)) for event_id in new_event_ids)
    detail = json.loads(detail)
    for index, trip_detail in enumerate(detail):
        if type(trip_detail) == str:
            if ast.literal_eval(trip_detail)['id'] == remove_event_id:
                remove_index = index
                break
        else:
            if trip_detail['id'] == remove_event_id:
                remove_index = index
                break
    detail.pop(remove_index)
    regular = False
    cur.execute("select * from day_trip_table_city where trip_locations_id='%s'" %(new_trip_locations_id))  
    check_id = cur.fetchone()
    if not check_id:
        cur.execute("select max(index) from day_trip_table_city;")
        new_index = cur.fetchone()[0]
        new_index+=1
        cur.execute("INSERT INTO day_trip_table_city VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s);" ,(new_index, new_trip_locations_id, full_day, regular, city, state, json.dumps(detail), event_type, json.dumps(new_event_ids)))  
        conn.commit()
    conn.close()
    new_full_trip_id, new_full_trip_details,new_trip_location_ids = new_full_trip_afer_remove_event(full_trip_id, trip_locations_id, new_trip_locations_id, username_id=1)
    return new_full_trip_id, new_full_trip_details,new_trip_location_ids, new_trip_locations_id

def new_full_trip_afer_remove_event(full_trip_id, old_trip_locations_id, new_trip_locations_id, username_id=1):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor() 
    username_id = 1
    cur.execute("SELECT trip_location_ids, regular, city, state, details, n_days FROM full_trip_table_city WHERE full_trip_id = '{}' LIMIT 1;".format(full_trip_id))
    trip_location_ids, regular, city, state, details, n_days = cur.fetchone()

    trip_location_ids = ast.literal_eval(trip_location_ids)
    trip_location_ids[:] = [new_trip_locations_id if x==old_trip_locations_id else x for x in trip_location_ids]
    new_full_trip_id = '-'.join(trip_location_ids)
    new_full_trip_details = []
    for trip_locations_id in trip_location_ids:
        cur.execute("SELECT details FROM day_trip_table_city WHERE trip_locations_id = '{}' LIMIT 1;".format(trip_locations_id))
        detail = cur.fetchone()[0]
        detail = json.loads(detail)
        new_full_trip_details.extend(detail)
    regular=False
    if not check_full_trip_id(new_full_trip_id):
        cur.execute("SELECT max(index) FROM full_trip_table_city;")
        full_trip_index = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO full_trip_table_city (index, username_id, full_trip_id,trip_location_ids, regular, city, state, details, n_days) VALUES (%s, %s, '%s', '%s', %s, '%s', '%s', '%s', %s);" %(full_trip_index, username_id, new_full_trip_id, json.dumps(trip_location_ids), regular, city, state, json.dumps(new_full_trip_details),n_days))
        conn.commit()
    conn.close()
    return new_full_trip_id, new_full_trip_details,trip_location_ids

def event_type_time_spent(adjusted_normal_time_spent):
    if adjusted_normal_time_spent > 180:
        return 'big', 
    elif adjusted_normal_time_spent >= 120:
        return 'med'
    else:
        return 'small'

#Model: get cloest events within a radius: min 3 same type of events (poi_type), 3 within the radius 10 mile, 3 same time spent
def suggest_event_array(full_trip_id, trip_location_id, switch_event_id, username_id,max_radius = 10*1609.34):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()   
    cur.execute("SELECT event_ids FROM day_trip_table_city WHERE trip_locations_id  = '%s' LIMIT 1;" %(trip_location_id))  
    old_event_ids = json.loads(cur.fetchone()[0])
    cur.execute("SELECT index, name, coord_lat, coord_long,poi_type, adjusted_visit_length,num_reviews FROM poi_detail_table where index=%s;" %(switch_event_id))
    index, name, coord_lat, coord_long,poi_type, adjusted_normal_time_spent,num_reviews = cur.fetchone()
    event_type = event_type_time_spent(adjusted_normal_time_spent)
    if event_type == 'big':
        cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and adjusted_visit_length>180 and poi_type='{0}' and index NOT IN {3} ORDER BY num_reviews LIMIT 7;".format(poi_type, coord_long,coord_lat,tuple(old_event_ids)))
    elif event_type == 'med':
        cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and adjusted_visit_length>=120 and adjusted_visit_length<=180 and poi_type='{0}' and index NOT IN {3} ORDER BY num_reviews LIMIT 7;".format(poi_type, coord_long,coord_lat,tuple(old_event_ids)))
    else:
        cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and adjusted_visit_length<120 and poi_type = '{0}' and index NOT IN {3} ORDER BY num_reviews LIMIT 7;".format(poi_type, coord_long,coord_lat,tuple(old_event_ids)))
    suggest_event_lst = cur.fetchall()
    rank_one_idx = [x[0] for x in suggest_event_lst]
    old_event_ids.extend(rank_one_idx)
    old_event_ids = map(int, old_event_ids)
    limit_len = min(7- len(suggest_event_lst), 3)
    if limit_len:
        cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and poi_type='{0}' and index not in {3} ORDER BY num_reviews LIMIT {4};".format(poi_type, coord_long,coord_lat, tuple(old_event_ids), limit_len))
        add_suggest_lst = cur.fetchall()
        if add_suggest_lst:
            suggest_event_lst.extend(add_suggest_lst)
            limit_len = min(7- len(suggest_event_lst), 3)
            rank_one_idx = [x[0] for x in suggest_event_lst]
            old_event_ids.extend(rank_one_idx)
            old_event_ids = map(int, old_event_ids)
            if limit_len:
                if event_type == 'big':
                    cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and adjusted_visit_length>180 and index NOT IN {3} ORDER BY num_reviews LIMIT {0};".format(limit_len, coord_long,coord_lat,tuple(old_event_ids)))
                elif event_type == 'med':
                    cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and adjusted_visit_length>=120 and adjusted_visit_length<=180 and index NOT IN {3} ORDER BY num_reviews LIMIT {0};".format(limit_len, coord_long,coord_lat,tuple(old_event_ids)))
                else:
                    cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 10 * 1609.34 and adjusted_visit_length<120 and index NOT IN {3} ORDER BY num_reviews LIMIT {0};".format(limit_len, coord_long,coord_lat,tuple(old_event_ids)))
                add_suggest_lst = cur.fetchall()
                if add_suggest_lst:
                    suggest_event_lst.extend(add_suggest_lst)
                    if 7- len(suggest_event_lst):
                        rank_one_idx = [x[0] for x in suggest_event_lst]
                        old_event_ids.extend(rank_one_idx)
                        old_event_ids = map(int, old_event_ids)
                        cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE poi_type='{0}' and index not in {3} ORDER BY ST_Distance_Sphere(geom, ST_MakePoint({1},{2}))   LIMIT {4};".format(poi_type, coord_long,coord_lat, tuple(old_event_ids), 7- len(suggest_event_lst)))
    suggest_dict_list = []
    for i, a in enumerate(suggest_event_lst):
        suggest_dict_list.append( {'id': a[0],'name': a[1],'address': a[2], 'coord_lat': a[3], 'coord_long': a[4], 'city': a[5], 'state': a[6], 'icon_url': a[7], 'check_full_address': a[8], 'poi_type': a[9], 'adjusted_visit_length': a[10], 'img_url': a[11]})
    conn.close()
    return suggest_dict_list

def convert_db_details(detail, remove_event_id):
    detail = ast.literal_eval(detail[1:-1])
    for index, trip_detail in enumerate(detail):
        if type(trip_detail) == str:
            if ast.literal_eval(trip_detail)['id'] == remove_event_id:
                remove_index = index
                break
        else:
            if trip_detail['id'] == remove_event_id:
                remove_index = index
                break

    new_detail = list(detail)
    new_detail.pop(remove_index)
    new_detail =  str(new_detail).replace("'","''")
    regular = False
    return 

def switch_suggest_event(full_trip_id, update_trip_location_id, update_suggest_event, username_id=1): 
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()   
    cur.execute("SELECT trip_location_ids FROM full_trip_table_city WHERE full_trip_id = '%s';" %(full_trip_id)) 
    trip_location_ids = json.loads(cur.fetchone()[0])
    trip_location_ids =[str(x) for x in trip_location_ids]
    update_suggest_event = json.loads(update_suggest_event)
    full_trip_details = []
    full_trip_trip_locations_id = []
    new_update_trip_location_id = ''
    for trip_location_id in trip_location_ids:
        cur.execute("SELECT * FROM day_trip_table_city WHERE trip_locations_id  = '%s' LIMIT 1;" %(trip_location_id)) 
        (index, trip_locations_id, full_day, regular, county, state, detail, event_type, event_ids) = cur.fetchone()
        event_ids = map(int, json.loads(event_ids))
        detail = json.loads(detail)
        full_day = True
        event_type = 'suggest'
        for idx, event_id in enumerate(event_ids):
            if str(event_id) in update_suggest_event:
                regular = False
                replace_event_detail = update_suggest_event[str(event_id)]
                replace_event_detail['day'] = detail[idx]['day']
                detail[idx] = replace_event_detail
                event_ids[idx] = replace_event_detail['id']
        if not regular:
            trip_locations_id = '-'.join(map(str,event_ids))
            if not check_day_trip_id_city(trip_locations_id):
                cur.execute("SELECT max(index) FROM day_trip_table_city;")
                new_index = cur.fetchone()[0] + 1
                cur.execute("INSERT INTO day_trip_table_city VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s);" ,(new_index, trip_locations_id, full_day, regular, county, state, json.dumps(detail),event_type,json.dumps(event_ids)))
                conn.commit()
        if update_trip_location_id == trip_location_id:
            new_update_trip_location_id = trip_locations_id
        full_trip_details.extend(detail)
        full_trip_trip_locations_id.append(trip_locations_id)
    if full_trip_trip_locations_id != trip_location_ids:
        new_full_trip_id = '-'.join(full_trip_trip_locations_id)
        if not check_full_trip_id(new_full_trip_id):
            n_days = len(trip_location_ids)
            regular =False
            cur.execute("SELECT max(index) FROM full_trip_table_city;")
            new_index = cur.fetchone()[0] + 1
            cur.execute("INSERT INTO full_trip_table_city VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",(new_index, username_id, new_full_trip_id, json.dumps(full_trip_trip_locations_id), regular, county, state, json.dumps(full_trip_details), n_days))
            conn.commit()
            conn.close()
        return new_full_trip_id, full_trip_details, full_trip_trip_locations_id, new_update_trip_location_id
    if new_update_trip_location_id == '':
        new_update_trip_location_id = update_trip_location_id
    return full_trip_id, full_trip_details, full_trip_trip_locations_id, new_update_trip_location_id
#using v1 front end design.
def create_full_trip(full_trip_id, username_id):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()
    # print "select * from full_trip_table where full_trip_id='%s' and username_id=%s;" %(full_trip_id, username_id)
    cur.execute("select count(1) from full_trip_table_city where full_trip_id='%s' and username_id=%s;" %(full_trip_id, username_id))  
    cnt = cur.fetchone()[0]
    if cnt != 0:
        return False
    else:
        cur.execute("SELECT max(index) from full_trip_table_city;")
        new_index = cur.fetchone()[0] + 1
        cur.execute("select * from full_trip_table_city where full_trip_id='%s';" %(full_trip_id))  
        # print "select * from full_trip_table where full_trip_id='%s';" %(full_trip_id)
        (index, old_username_id, full_trip_id,trip_location_ids, regular, county, state, details, n_days) = cur.fetchone()
        cur.execute("INSERT INTO full_trip_table_city VALUES (%s, %s, '%s', '%s', %s, '%s', '%s', '%s', %s);" %(new_index, username_id, full_trip_id, trip_location_ids.replace("'",'"'), regular, county, state, details.replace("'",'"'), n_days))
        conn.commit()
        conn.close()
        return True
