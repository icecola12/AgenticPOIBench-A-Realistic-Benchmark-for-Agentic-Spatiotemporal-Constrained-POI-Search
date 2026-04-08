"""
修改任务指令：你要在附近2500米以内找一家自习室。你打算骑共享单车过去，所以从你这里骑行到自习室的距离不能超过1500米。自习室周围1500米内会有一些公交站，你希望从自习室步行到这些公交站里最近的一个，步行距离不要超过600米。另外你要赶去“聊城站”接人，所以自习室到“顺德大厦(公交站)”的直线距离不能超过200米。你还想在从你这到自习室的路上顺便买点东西，所以你到自习室的骑行路线上，需要至少存在一个途径点，该途径点的200米范围内要能找到便利店。最后你不想绕路太多：从你这里先去自习室再去聊城站的总驾车时间，相比你直接从你这里开车去聊城站，增加的时间不要超过2分钟。你说话非常有条理和注重细节
输入：B0H2RZ3IRI
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2500米内：调用 maps_around_search(location='116.012798,36.455486', radius='2500', keywords='自习室')，验证返回结果中包含 target_poi_id='B0H2RZ3IRI'。
2) 评分：调用 maps_search_detail(id='B0H2RZ3IRI') 获取 biz_ext.rating，验证 rating >= 4.1（该POI详情返回为4.1）。
3) 骑行距离上限：调用 maps_bicycling_by_coordinates(origin='116.012798,36.455486', destination='116.025051,36.456945')，验证 total_distance_meters <= 1500（实测1112m）。
4) 最近公交站步行距离：
a. 调用 maps_around_search(location='116.025051,36.456945', radius='1500', keywords='公交站') 获取候选公交站列表；
b. 对每个公交站POI坐标调用 maps_walking_by_coordinates(origin='116.025051,36.456945', destination='<bus_stop_location>')，取步行距离最小值min_d；
c. 验证 min_d <= 600m
5) 到指定公交站点直线距离：
a. 调用 maps_text_search(keywords='顺德大厦(公交站)', city='聊城', citylimit='true') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 该站点POI id与坐标（再用 maps_search_detail 获取其location，如需）；
b. 调用 maps_distance(origins='116.025051,36.456945', destination='116.023672,36.457561')，验证 distance_meters <= 200（实测141m）。
6) 途径点附近200米有“便利店”：
a. 取一处途径点坐标 vp='116.019000,36.456200'（可作为骑行路线中间点的候选）；
b. 调用 maps_around_search(location=vp, radius='200', keywords='便利店')，验证返回pois非空（实测包含“易捷便利店”B0GRGYNSB4）。
7) 绕路时间增量不超过2分钟：
a. 用 maps_text_search(keywords='聊城站', city='聊城') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 聊城站坐标 ls；
b. 调用 maps_driving_by_coordinates(origin='116.012798,36.455486', destination=ls) 得到 t_direct；
c. 调用 maps_driving_by_coordinates(origin='116.012798,36.455486', destination='116.025051,36.456945') 得到 t_A；
d. 调用 maps_driving_by_coordinates(origin='116.025051,36.456945', destination=ls) 得到 t_B；
e. 验证 (t_A + t_B - t_direct) <= 120秒（实测：t_A=160s, t_B=611s, t_direct=715s，增量=56s）。
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
    maps_driving_by_coordinates ,
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
    target_poi_id: str = "B0H2RZ3IRI",
    user_location: str = "116.012798,36.455486",
    radius: str = "2500",
    keywords: str = "自习室",
    min_rating: float = 4.1,
    max_bicycling_distance: int = 1500,
    bus_search_radius: str = "1500",
    bus_keywords: str = "公交站",
    max_walking_distance_to_bus: int = 600,
    bus_stop_keywords: str = "顺德大厦(公交站)",
    bus_stop_city: str = "聊城",
    bus_stop_citylimit: str = "true",
    max_distance_to_bus_stop: int = 200,
    waypoint_location: str = "116.019000,36.456200",
    convenience_store_radius: str = "200",
    convenience_store_keywords: str = "便利店",
    station_address: str = "聊城站",
    station_city: str = "聊城",
    max_detour_time: int = 120
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        min_rating: 最小评分
        max_bicycling_distance: 最大骑行距离（米）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_walking_distance_to_bus: 到最近公交站的最大步行距离（米）
        bus_stop_keywords: 指定公交站搜索关键词
        bus_stop_city: 公交站所在城市
        bus_stop_citylimit: 是否限制城市
        max_distance_to_bus_stop: 到指定公交站的最大直线距离（米）
        waypoint_location: 途径点坐标
        convenience_store_radius: 便利店搜索半径（米）
        convenience_store_keywords: 便利店搜索关键词
        station_address: 车站地址
        station_city: 车站所在城市
        max_detour_time: 最大绕路时间增量（秒）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 步骤1: 附近2500米内
    print(f"步骤1: 验证附近{radius}米内的周边搜索约束 - 查询POI ID: {target_poi_id}")
    around_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )
    
    if around_result.error:
        print(f"步骤1失败: {around_result.error}")
        return False
    
    if not around_result.pois:
        print("步骤1失败: 未找到任何POI")
        return False
    
    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")
    
    # 步骤2: 评分
    print(f"\n步骤2: 验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        print("错误: 无法获取POI详情，无法继续验证")
        return False
    
    # 获取POI坐标（后续步骤需要）
    if not poi_detail.location:
        print("错误: 未获取到POI坐标，无法继续验证")
        return False
    
    poi_location = poi_detail.location
    print(f"POI坐标: {poi_location}")
    
    if not poi_detail.biz_ext:
        print("步骤2失败: 未获取到POI扩展信息")
        all_passed = False
    else:
        rating = poi_detail.biz_ext.get('rating')
        if rating is None:
            print("步骤2失败: 未获取到评分信息")
            all_passed = False
        else:
            try:
                rating_value = float(rating)
                if rating_value < min_rating:
                    print(f"步骤2失败: 评分{rating_value}小于要求{min_rating}")
                    all_passed = False
                else:
                    print(f"步骤2通过: 评分{rating_value}，满足要求（>={min_rating}）")
            except (ValueError, TypeError):
                print(f"步骤2失败: 评分格式错误: {rating}")
                all_passed = False
    
    # 步骤3: 骑行距离上限
    print(f"\n步骤3: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    
    if bicycling_result.error:
        print(f"步骤3失败: {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is None:
            print("步骤3失败: 未获取到骑行距离")
            all_passed = False
        else:
            bicycling_distance = bicycling_result.total_distance_meters
            if bicycling_distance > max_bicycling_distance:
                print(f"步骤3失败: 骑行距离{bicycling_distance}米超过要求{max_bicycling_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 骑行距离{bicycling_distance}米，满足要求（<={max_bicycling_distance}米）")
    
    # 步骤4: 最近公交站步行距离
    print(f"\n步骤4: 验证最近公交站步行距离不超过{max_walking_distance_to_bus}米")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )
    
    if bus_around_result.error:
        print(f"步骤4失败: {bus_around_result.error}")
        all_passed = False
    else:
        if not bus_around_result.pois or len(bus_around_result.pois) == 0:
            print(f"步骤4失败: 未找到任何{bus_keywords}")
            all_passed = False
        else:
            # 遍历公交站，找到步行距离最小的
            min_walking_distance = None
            for bus_poi in bus_around_result.pois:
                bus_detail = maps_search_detail(id=bus_poi.id)
                if bus_detail.error or not bus_detail.location:
                    continue
                
                bus_location = bus_detail.location
                walking_result = maps_walking_by_coordinates(
                    origin=poi_location,
                    destination=bus_location
                )
                
                if walking_result.error or walking_result.total_distance_meters is None:
                    continue
                
                distance = walking_result.total_distance_meters
                if min_walking_distance is None or distance < min_walking_distance:
                    min_walking_distance = distance
            
            if min_walking_distance is None:
                print(f"步骤4失败: 无法计算到任何{bus_keywords}的步行距离")
                all_passed = False
            elif min_walking_distance > max_walking_distance_to_bus:
                print(f"步骤4失败: 最近{bus_keywords}步行距离{min_walking_distance}米超过要求{max_walking_distance_to_bus}米")
                all_passed = False
            else:
                print(f"步骤4通过: 最近{bus_keywords}步行距离{min_walking_distance}米，满足要求（<={max_walking_distance_to_bus}米）")
    
    # 步骤5: 到指定公交站点直线距离
    print(f"\n步骤5: 验证到指定公交站点直线距离不超过{max_distance_to_bus_stop}米")
    text_search_result = maps_text_search(
        keywords=bus_stop_keywords,
        city=bus_stop_city,
        citylimit=bus_stop_citylimit
    )
    
    if text_search_result.error:
        print(f"步骤5失败: 搜索公交站失败 - {text_search_result.error}")
        all_passed = False
    else:
        if not text_search_result.pois or len(text_search_result.pois) == 0:
            print(f"步骤5失败: 未找到'{bus_stop_keywords}'")
            all_passed = False
        else:
            # 获取公交站坐标
            bus_stop_poi = text_search_result.pois[0]
            bus_stop_detail = maps_search_detail(id=bus_stop_poi.id)
            
            if bus_stop_detail.error or not bus_stop_detail.location:
                print(f"步骤5失败: 获取公交站坐标失败")
                all_passed = False
            else:
                bus_stop_location = bus_stop_detail.location
                distance_result = maps_distance(
                    origins=poi_location,
                    destination=bus_stop_location
                )
                
                if distance_result.error:
                    print(f"步骤5失败: 计算距离失败 - {distance_result.error}")
                    all_passed = False
                else:
                    if not distance_result.results or len(distance_result.results) == 0:
                        print("步骤5失败: 未获取到距离结果")
                        all_passed = False
                    else:
                        distance = distance_result.results[0].distance_meters
                        if distance > max_distance_to_bus_stop:
                            print(f"步骤5失败: 到公交站的距离{distance}米超过要求{max_distance_to_bus_stop}米")
                            all_passed = False
                        else:
                            print(f"步骤5通过: 到公交站的距离{distance}米，满足要求（<={max_distance_to_bus_stop}米）")
    
    # 步骤6: 途径点附近200米有"便利店"
    print(f"\n步骤6: 验证途径点附近{convenience_store_radius}米有{convenience_store_keywords}")
    convenience_store_result = maps_around_search(
        location=waypoint_location,
        radius=convenience_store_radius,
        keywords=convenience_store_keywords
    )
    
    if convenience_store_result.error:
        print(f"步骤6失败: {convenience_store_result.error}")
        all_passed = False
    else:
        if not convenience_store_result.pois or len(convenience_store_result.pois) == 0:
            print(f"步骤6失败: 途径点附近未找到{convenience_store_keywords}")
            all_passed = False
        else:
            store_count = len(convenience_store_result.pois)
            print(f"步骤6通过: 途径点附近找到{store_count}个{convenience_store_keywords}，满足要求（数量>0）")
    
    # 步骤7: 绕路时间增量不超过2分钟
    print(f"\n步骤7: 验证绕路时间增量不超过{max_detour_time}秒（{max_detour_time//60}分钟）")
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"步骤7失败: 获取{station_address}坐标失败 - {station_text_result.error}")
        all_passed = False
    else:
        if not station_text_result.pois or len(station_text_result.pois) == 0:
            print(f"步骤7失败: 未找到{station_address}坐标")
            all_passed = False
        else:
            first_poi_id = station_text_result.pois[0].id
            station_detail_result = maps_search_detail(id=first_poi_id)
            if station_detail_result.error:
                print(f"❌ 获取坐标失败: {station_detail_result.error}")
                all_passed = False
            elif not station_detail_result.location:
                print("❌ 未获取到坐标")
                all_passed = False
            else:
                station_location = station_detail_result.location
            print(f"{station_address}坐标: {station_location}")
            
            # 计算直接驾车时间 t_direct
            driving_result_direct = maps_driving_by_coordinates(
                origin=user_location,
                destination=station_location
            )
            
            if driving_result_direct.error or driving_result_direct.total_duration_seconds is None:
                print(f"步骤7失败: 计算直接驾车时间失败")
                all_passed = False
            else:
                t_direct = driving_result_direct.total_duration_seconds
                
                # 计算用户到POI的驾车时间 t_A
                driving_result_A = maps_driving_by_coordinates(
                    origin=user_location,
                    destination=poi_location
                )
                
                if driving_result_A.error or driving_result_A.total_duration_seconds is None:
                    print(f"步骤7失败: 计算用户到POI驾车时间失败")
                    all_passed = False
                else:
                    t_A = driving_result_A.total_duration_seconds
                    
                    # 计算POI到车站的驾车时间 t_B
                    driving_result_B = maps_driving_by_coordinates(
                        origin=poi_location,
                        destination=station_location
                    )
                    
                    if driving_result_B.error or driving_result_B.total_duration_seconds is None:
                        print(f"步骤7失败: 计算POI到车站驾车时间失败")
                        all_passed = False
                    else:
                        t_B = driving_result_B.total_duration_seconds
                        
                        # 计算绕路时间增量
                        detour_time = t_A + t_B - t_direct
                        if detour_time > max_detour_time:
                            print(f"步骤7失败: 绕路时间增量{detour_time}秒超过要求{max_detour_time}秒（t_A={t_A}秒, t_B={t_B}秒, t_direct={t_direct}秒）")
                            all_passed = False
                        else:
                            print(f"步骤7通过: 绕路时间增量{detour_time}秒，满足要求（<={max_detour_time}秒）（t_A={t_A}秒, t_B={t_B}秒, t_direct={t_direct}秒）")
    
    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
