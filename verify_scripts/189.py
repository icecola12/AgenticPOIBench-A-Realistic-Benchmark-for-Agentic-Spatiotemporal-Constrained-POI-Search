"""
修改任务指令：你想在附近2000米内找一个加油站。加油站离河北枣强第二中学的直线距离不少于500米。你从家开车去加油站的路线上需要至少存在一个加油站满足附近300米存在超市。加油站附近1000米至少存在一个公交站满足到加油站的直线距离不超过300米。你加完油还要去枣强站接朋友，所以从家出发，先到加油站再到火车站，总时间不能超过15分钟。而且绕道加油站增加的时间不能超过2分钟。另外，你从家出发和朋友从枣强县人民医院出发到加油站的时间差不能超过5分钟。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
输入：B013E00D1Y
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('115.737244,37.522709', '加油站', 2000)验证目标加油站在搜索范围内。
2. 调用maps_search_detail('B013E00D1Y')获取加油站坐标(115.738839,37.520440)。
3. 调用maps_search_detail('B013E0038Q')获取河北枣强第二中学坐标(115.726827,37.518462)，调用maps_distance('115.738839,37.520440', '115.726827,37.518462')验证距离≥500米。
4. 调用maps_driving_by_coordinates('115.737244,37.522709', '115.738839,37.520440')获取驾车路线steps，遍历途经点如(115.736258,37.520074)，调用maps_around_search('115.736258,37.520074', '超市', 300)验证附近300米有超市。
5. 调用maps_around_search('115.738839,37.520440', '公交站', 1000)获取附近公交站列表，遍历公交站列表，先验证返回列表不为空，并调用maps_distance验证至少存在一个途径点直线距离≤300米。
6. 调用maps_driving_by_coordinates('115.737244,37.522709', '115.738839,37.520440')获取时间t1，调用maps_driving_by_coordinates('115.738839,37.520440', '115.738258,37.504443')获取时间t2，计算总时间(t1+t2)≤15分钟(900秒)。
7. 调用maps_driving_by_coordinates('115.737244,37.522709', '115.738258,37.504443')获取直达时间t_direct，计算绕行增加时间(t1+t2 - t_direct)≤2分钟(120秒)。
8. 调用maps_driving_by_coordinates('115.731451,37.498006', '115.738839,37.520440')获取从医院到加油站时间t_hospital，计算与t1的差值绝对值|t_hospital - t1|≤5分钟(300秒)。
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates,
    maps_geo,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B013E00D1Y",
    user_location: str = "115.737244,37.522709",
    around_search_radius: str = "2000",
    around_search_keywords: str = "加油站",
    school_poi_id: str = "B013E0038Q",
    min_distance_to_school_meters: int = 500,
    route_supermarket_radius: str = "300",
    route_supermarket_keywords: str = "超市",
    bus_station_search_radius: str = "1000",
    bus_station_keywords: str = "公交站",
    max_bus_station_distance_meters: int = 300,
    max_total_driving_seconds: int = 900,
    max_detour_seconds: int = 120,
    max_time_diff_seconds: int = 300,
    station_keywords: str = "枣强站",
    station_city: str = "枣强",
    hospital_keywords: str = "枣强县人民医院",
    hospital_city: str = "枣强"
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID（加油站）
        user_location: 用户位置坐标，格式为"经度,纬度"
        around_search_radius: 周边搜索半径（米）
        around_search_keywords: 周边搜索关键词
        school_poi_id: 学校POI ID
        min_distance_to_school_meters: 到学校的最小距离（米）
        route_supermarket_radius: 路线途经点超市搜索半径（米）
        route_supermarket_keywords: 路线途经点超市搜索关键词
        bus_station_search_radius: 公交站搜索半径（米）
        bus_station_keywords: 公交站搜索关键词
        max_bus_station_distance_meters: 公交站到加油站的最大直线距离（米）
        max_total_driving_seconds: 最大总驾车时间（秒）
        max_detour_seconds: 最大绕路时间（秒）
        max_time_diff_seconds: 最大时间差（秒）
        station_keywords: 火车站搜索关键词
        station_city: 火车站所在城市
        hospital_keywords: 医院搜索关键词
        hospital_city: 医院所在城市
    
    Returns:
        bool: True表示所有验证都通过，False表示有验证未通过
    """
    all_passed = True
    
    # 验证步骤1: 检查目标加油站是否在2000米范围内
    print("=" * 50)
    print("验证步骤1: 检查目标加油站是否在2000米范围内")
    print(f"调用 maps_around_search(location='{user_location}', radius='{around_search_radius}', keywords='{around_search_keywords}')")
    around_result = maps_around_search(location=user_location, radius=around_search_radius, keywords=around_search_keywords)
    
    if around_result.error:
        print(f"验证步骤1: 未通过 - 周边搜索失败: {around_result.error}")
        all_passed = False
    elif not around_result.pois:
        print("验证步骤1: 未通过 - 周边搜索未找到POI")
        all_passed = False
    else:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"验证步骤1: 通过 - target_poi_id {target_poi_id} 在周边POI列表中（共{len(poi_ids)}个POI）")
        else:
            print(f"验证步骤1: 未通过 - target_poi_id {target_poi_id} 不在周边POI列表中")
            all_passed = False
    
    # 验证步骤2: 获取目标加油站的精确坐标
    print("=" * 50)
    print("验证步骤2: 获取目标加油站的精确坐标")
    print(f"调用 maps_search_detail(id='{target_poi_id}')")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"验证步骤2: 未通过 - POI详情查询失败: {detail_result.error}")
        all_passed = False
        return False
    
    if not detail_result.location:
        print("验证步骤2: 未通过 - 无法获取POI坐标，后续验证无法进行")
        return False
    
    gas_station_location = detail_result.location
    print(f"验证步骤2: 通过 - 获取到加油站坐标: {gas_station_location}")
    
    # 验证步骤3: 验证加油站离河北枣强第二中学的直线距离不少于500米
    print("=" * 50)
    print("验证步骤3: 验证加油站离河北枣强第二中学的直线距离不少于500米")
    print(f"调用 maps_search_detail(id='{school_poi_id}')")
    school_detail_result = maps_search_detail(id=school_poi_id)
    
    if school_detail_result.error:
        print(f"验证步骤3: 未通过 - 学校POI详情查询失败: {school_detail_result.error}")
        all_passed = False
    elif not school_detail_result.location:
        print("验证步骤3: 未通过 - 无法获取学校坐标")
        all_passed = False
    else:
        school_location = school_detail_result.location
        print(f"获取到学校坐标: {school_location}")
        print(f"调用 maps_distance(origins='{gas_station_location}', destination='{school_location}')")
        distance_result = maps_distance(origins=gas_station_location, destination=school_location)
        
        if distance_result.error or not distance_result.results:
            print(f"验证步骤3: 未通过 - 距离计算失败: {distance_result.error if distance_result.error else '未找到结果'}")
            all_passed = False
        else:
            distance_meters = distance_result.results[0].distance_meters
            print(f"加油站到学校的直线距离: {distance_meters}米")
            if distance_meters >= min_distance_to_school_meters:
                print(f"验证步骤3: 通过 - 距离 {distance_meters}米 >= {min_distance_to_school_meters}米")
            else:
                print(f"验证步骤3: 未通过 - 距离 {distance_meters}米 < {min_distance_to_school_meters}米")
                all_passed = False
    
    # 验证步骤4: 验证驾车路线途径点中至少有一个满足附近300米有超市
    print("=" * 50)
    print("验证步骤4: 验证驾车路线途径点中至少有一个满足附近300米有超市")
    print(f"调用 maps_driving_by_coordinates(origin='{user_location}', destination='{gas_station_location}')")
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=gas_station_location)
    
    if driving_result.error:
        print(f"验证步骤4: 未通过 - 驾车路线规划失败: {driving_result.error}")
        all_passed = False
    elif not driving_result.steps:
        print("验证步骤4: 未通过 - 驾车路线没有步骤信息")
        all_passed = False
    else:
        found_supermarket = False
        for step in driving_result.steps:
            # 使用步骤的终点坐标作为途径点
            waypoint = step.to_coordinates
            print(f"检查途径点: {waypoint}")
            supermarket_result = maps_around_search(location=waypoint, radius=route_supermarket_radius, keywords=route_supermarket_keywords)
            
            if supermarket_result.error:
                print(f"  途径点 {waypoint} 超市搜索失败: {supermarket_result.error}")
                continue
            
            if supermarket_result.pois and len(supermarket_result.pois) > 0:
                print(f"  途径点 {waypoint} 附近{route_supermarket_radius}米内找到{len(supermarket_result.pois)}个超市")
                found_supermarket = True
                break
        
        if found_supermarket:
            print(f"验证步骤4: 通过 - 找到至少一个途径点满足附近{route_supermarket_radius}米内有超市")
        else:
            print(f"验证步骤4: 未通过 - 所有途径点附近{route_supermarket_radius}米内都没有超市")
            all_passed = False
    
    # 验证步骤5: 验证加油站附近1000米至少存在一个公交站满足到加油站的直线距离不超过300米
    print("=" * 50)
    print("验证步骤5: 验证加油站附近1000米至少存在一个公交站满足到加油站的直线距离不超过300米")
    print(f"调用 maps_around_search(location='{gas_station_location}', radius='{bus_station_search_radius}', keywords='{bus_station_keywords}')")
    bus_station_result = maps_around_search(location=gas_station_location, radius=bus_station_search_radius, keywords=bus_station_keywords)
    
    if bus_station_result.error:
        print(f"验证步骤5: 未通过 - 公交站搜索失败: {bus_station_result.error}")
        all_passed = False
    elif not bus_station_result.pois or len(bus_station_result.pois) == 0:
        print("验证步骤5: 未通过 - 未找到公交站")
        all_passed = False
    else:
        print(f"找到{len(bus_station_result.pois)}个公交站，开始验证直线距离")
        found_valid_bus_station = False
        for bus_poi in bus_station_result.pois:
            if not bus_poi.location:
                continue
            
            print(f"调用 maps_distance(origins='{bus_poi.location}', destination='{gas_station_location}')")
            bus_distance_result = maps_distance(origins=bus_poi.location, destination=gas_station_location)
            
            if bus_distance_result.error or not bus_distance_result.results:
                print(f"  公交站 {bus_poi.name} 距离计算失败: {bus_distance_result.error if bus_distance_result.error else '未找到结果'}")
                continue
            
            bus_distance_meters = bus_distance_result.results[0].distance_meters
            print(f"  公交站 {bus_poi.name} 到加油站直线距离: {bus_distance_meters}米")
            
            if bus_distance_meters <= max_bus_station_distance_meters:
                print(f"  公交站 {bus_poi.name} 满足条件（距离 {bus_distance_meters}米 <= {max_bus_station_distance_meters}米）")
                found_valid_bus_station = True
                break
        
        if found_valid_bus_station:
            print(f"验证步骤5: 通过 - 找到至少一个公交站满足到加油站直线距离 <= {max_bus_station_distance_meters}米")
        else:
            print(f"验证步骤5: 未通过 - 所有公交站到加油站的直线距离都 > {max_bus_station_distance_meters}米")
            all_passed = False
    
    # 验证步骤6: 验证从家出发，先到加油站再到火车站，总时间不超过15分钟
    print("=" * 50)
    print("验证步骤6: 验证从家出发，先到加油站再到火车站，总时间不超过15分钟")
    
    # 获取火车站坐标
    print(f"调用 maps_text_search(keywords='{station_keywords}', city='{station_city}')")
    station_text_result = maps_text_search(keywords=station_keywords, city=station_city)
    
    if station_text_result.error or not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"验证步骤6: 未通过 - 无法获取火车站坐标: {station_text_result.error if station_text_result.error else '未找到POI'}")
        all_passed = False
    else:
        # 需要获取火车站的坐标，但text_search返回的POI没有location字段，需要再调用detail
        station_poi_id = station_text_result.pois[0].id
        print(f"获取到火车站POI ID: {station_poi_id}")
        print(f"调用 maps_search_detail(id='{station_poi_id}')")
        station_detail_result = maps_search_detail(id=station_poi_id)
        
        if station_detail_result.error or not station_detail_result.location:
            print(f"验证步骤6: 未通过 - 无法获取火车站坐标: {station_detail_result.error if station_detail_result.error else '无坐标信息'}")
            all_passed = False
        else:
            station_location = station_detail_result.location
            print(f"获取到火车站坐标: {station_location}")
            
            # 计算用户位置到加油站的驾车时间t1
            print(f"调用 maps_driving_by_coordinates(origin='{user_location}', destination='{gas_station_location}')")
            driving_result1 = maps_driving_by_coordinates(origin=user_location, destination=gas_station_location)
            
            if driving_result1.error or driving_result1.total_duration_seconds is None:
                print(f"验证步骤6: 未通过 - 用户到加油站驾车路线规划失败: {driving_result1.error if driving_result1.error else '无时间信息'}")
                all_passed = False
            else:
                t1 = driving_result1.total_duration_seconds
                print(f"用户到加油站驾车时间t1: {t1}秒")
                
                # 计算加油站到火车站的驾车时间t2
                print(f"调用 maps_driving_by_coordinates(origin='{gas_station_location}', destination='{station_location}')")
                driving_result2 = maps_driving_by_coordinates(origin=gas_station_location, destination=station_location)
                
                if driving_result2.error or driving_result2.total_duration_seconds is None:
                    print(f"验证步骤6: 未通过 - 加油站到火车站驾车路线规划失败: {driving_result2.error if driving_result2.error else '无时间信息'}")
                    all_passed = False
                else:
                    t2 = driving_result2.total_duration_seconds
                    print(f"加油站到火车站驾车时间t2: {t2}秒")
                    
                    total_time = t1 + t2
                    if total_time <= max_total_driving_seconds:
                        print(f"验证步骤6: 通过 - 总驾车时间 {total_time}秒 <= {max_total_driving_seconds}秒")
                    else:
                        print(f"验证步骤6: 未通过 - 总驾车时间 {total_time}秒 > {max_total_driving_seconds}秒")
                        all_passed = False
                    
                    # 验证步骤7: 验证绕路时间不超过2分钟
                    print("=" * 50)
                    print("验证步骤7: 验证绕路时间不超过2分钟")
                    print(f"调用 maps_driving_by_coordinates(origin='{user_location}', destination='{station_location}')")
                    driving_result3 = maps_driving_by_coordinates(origin=user_location, destination=station_location)
                    
                    if driving_result3.error or driving_result3.total_duration_seconds is None:
                        print(f"验证步骤7: 未通过 - 直接驾车路线规划失败: {driving_result3.error if driving_result3.error else '无时间信息'}")
                        all_passed = False
                    else:
                        t_direct = driving_result3.total_duration_seconds
                        print(f"直接驾车时间t_direct: {t_direct}秒")
                        
                        detour_time = total_time - t_direct
                        if detour_time <= max_detour_seconds:
                            print(f"验证步骤7: 通过 - 绕路时间 {detour_time}秒 <= {max_detour_seconds}秒")
                        else:
                            print(f"验证步骤7: 未通过 - 绕路时间 {detour_time}秒 > {max_detour_seconds}秒")
                            all_passed = False
    
    # 验证步骤8: 验证用户和朋友从医院出发到加油站的时间差不超过5分钟
    print("=" * 50)
    print("验证步骤8: 验证用户和朋友从医院出发到加油站的时间差不超过5分钟")
    
    # 获取医院坐标
    print(f"调用 maps_text_search(keywords='{hospital_keywords}', city='{hospital_city}')")
    hospital_text_result = maps_text_search(keywords=hospital_keywords, city=hospital_city)
    
    if hospital_text_result.error or not hospital_text_result.pois or len(hospital_text_result.pois) == 0:
        print(f"验证步骤8: 未通过 - 无法获取医院坐标: {hospital_text_result.error if hospital_text_result.error else '未找到POI'}")
        all_passed = False
    else:
        # 需要获取医院的坐标
        hospital_poi_id = hospital_text_result.pois[0].id
        print(f"获取到医院POI ID: {hospital_poi_id}")
        print(f"调用 maps_search_detail(id='{hospital_poi_id}')")
        hospital_detail_result = maps_search_detail(id=hospital_poi_id)
        
        if hospital_detail_result.error or not hospital_detail_result.location:
            print(f"验证步骤8: 未通过 - 无法获取医院坐标: {hospital_detail_result.error if hospital_detail_result.error else '无坐标信息'}")
            all_passed = False
        else:
            hospital_location = hospital_detail_result.location
            print(f"获取到医院坐标: {hospital_location}")
            
            # 计算用户从家到加油站的驾车时间t1
            print(f"调用 maps_driving_by_coordinates(origin='{user_location}', destination='{gas_station_location}')")
            driving_result_user = maps_driving_by_coordinates(origin=user_location, destination=gas_station_location)
            
            if driving_result_user.error or driving_result_user.total_duration_seconds is None:
                print(f"验证步骤8: 未通过 - 用户驾车路线规划失败: {driving_result_user.error if driving_result_user.error else '无时间信息'}")
                all_passed = False
            else:
                t1 = driving_result_user.total_duration_seconds
                print(f"用户驾车时间t1: {t1}秒")
                
                # 计算朋友从医院到加油站的驾车时间t_hospital
                print(f"调用 maps_driving_by_coordinates(origin='{hospital_location}', destination='{gas_station_location}')")
                driving_result_hospital = maps_driving_by_coordinates(origin=hospital_location, destination=gas_station_location)
                
                if driving_result_hospital.error or driving_result_hospital.total_duration_seconds is None:
                    print(f"验证步骤8: 未通过 - 医院到加油站驾车路线规划失败: {driving_result_hospital.error if driving_result_hospital.error else '无时间信息'}")
                    all_passed = False
                else:
                    t_hospital = driving_result_hospital.total_duration_seconds
                    print(f"医院到加油站驾车时间t_hospital: {t_hospital}秒")
                    
                    time_diff = abs(t1 - t_hospital)
                    if time_diff <= max_time_diff_seconds:
                        print(f"验证步骤8: 通过 - 时间差 {time_diff}秒 <= {max_time_diff_seconds}秒")
                    else:
                        print(f"验证步骤8: 未通过 - 时间差 {time_diff}秒 > {max_time_diff_seconds}秒")
                        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
