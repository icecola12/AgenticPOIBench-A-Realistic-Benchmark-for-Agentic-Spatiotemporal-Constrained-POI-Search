"""
修改任务指令：你想在附近2000米内找一个电竞馆，评分要高于4.0。这个电竞馆离西安交通大学的直接距离要超过500米。你从当前位置开车过去路线的途径点中，至少需要存在一个途径点满足离黄雁村地铁站直线距离500米以内。另外，电竞馆附近200米内要有地铁站。你之后需要从西安火车站接个朋友，然后一起去电竞馆，再送他去西安北站，整个开车时间不能超过40分钟。还有，你两个朋友分别从西北工业大学和西安体育学院骑自行车过来，他们到达电竞馆的时间差不能超过5分钟。你依赖心强，希望智能体能为自己处理和决定一切。
输入：B0FFF64XDQ
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用 maps_around_search('108.923438,34.234728', '电竞馆', 2000) 检查目标 POI 是否在搜索结果中。
2. 调用 maps_search_detail('B0FFF64XDQ') 获取坐标、评分等信息，验证评分 > 4.0。
3. 调用 maps_text_search('西安交通大学', '西安') 获取交大 POI ID，再调用 maps_search_detail 获取其坐标，然后调用 maps_distance 计算目标 POI 到交大的直线距离，验证 > 500 米。
4. 调用 maps_driving_by_coordinates('108.923438,34.234728', '108.932482,34.239588') 获取驾车路线 steps，遍历steps，对from_coordinates 和 to_coordinates（不包括起点和终点），调用 maps_distance 计算到黄雁村地铁站('108.933281,34.241154')的直线距离，验证存在至少一个点距离 < 500 米。
5. 调用 maps_distance 计算目标 POI 到黄雁村地铁站的直线距离，验证 < 200 米。
6. 调用 maps_driving_by_coordinates 计算西安火车站('108.962723,34.278498')到目标 POI 的驾车时间 t1，计算目标 POI 到西安北站('108.938757,34.376660')的驾车时间 t2，验证 (t1 + t2) ≤ 40 分钟（2400 秒）。
7. 调用 maps_bicycling_by_coordinates 计算西北工业大学('108.915423,34.243699')到目标 POI 的骑行时间 t3，计算西安体育学院('108.935090,34.237611')到目标 POI 的骑行时间 t4，验证 |t3 - t4| ≤ 5 分钟（300 秒）。
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
    target_poi_id: str = 'B0FFF64XDQ',
    user_location: str = '108.923438,34.234728',
    search_keywords: str = '电竞馆',
    search_radius: str = '2000',
    huangyancun_station: str = '108.933281,34.241154',
    xian_train_station: str = '108.962723,34.278498',
    xian_north_station: str = '108.938757,34.376660',
    nwpu_location: str = '108.915423,34.243699',
    xian_sport_location: str = '108.935090,34.237611',
    jiaoda_keywords: str = '西安交通大学',
    jiaoda_city: str = '西安'
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_keywords: 搜索关键词
        search_radius: 搜索半径（米）
        huangyancun_station: 黄雁村地铁站坐标
        xian_train_station: 西安火车站坐标
        xian_north_station: 西安北站坐标
        nwpu_location: 西北工业大学坐标
        xian_sport_location: 西安体育学院坐标
        jiaoda_keywords: 交大搜索关键词
        jiaoda_city: 交大搜索城市
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True
    
    # 验证步骤1: 检查目标 POI 是否在周边搜索结果中
    print("验证步骤1: 检查目标 POI 是否在周边搜索结果中...")
    around_result = maps_around_search(user_location, search_radius, search_keywords)
    if around_result.error:
        print(f"  验证失败: {around_result.error}")
        all_passed = False
    elif around_result.pois:
        poi_ids = [poi.id for poi in around_result.pois]
        if target_poi_id in poi_ids:
            print(f"  验证通过: 目标 POI {target_poi_id} 在搜索结果中")
        else:
            print(f"  验证失败: 目标 POI {target_poi_id} 不在搜索结果中")
            all_passed = False
    else:
        print("  验证失败: 搜索结果为空")
        all_passed = False
    
    # 验证步骤2: 验证评分 > 4.0
    print("验证步骤2: 验证评分 > 4.0...")
    detail_result = maps_search_detail(target_poi_id)
    if detail_result.error:
        print(f"  验证失败: {detail_result.error}")
        all_passed = False
    else:
        # 获取目标POI坐标，后续步骤需要用到
        target_poi_location = detail_result.location
        if not target_poi_location:
            print("  验证失败: 无法获取目标 POI 坐标")
            all_passed = False
        else:
            # 检查评分
            rating = None
            if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
                rating_str = detail_result.biz_ext.get('rating', '')
                if rating_str:
                    try:
                        rating = float(rating_str)
                    except (ValueError, TypeError):
                        pass
            
            if rating is not None:
                if rating > 4.0:
                    print(f"  验证通过: 评分 {rating} > 4.0")
                else:
                    print(f"  验证失败: 评分 {rating} <= 4.0")
                    all_passed = False
            else:
                print("  验证失败: 无法获取评分信息")
                all_passed = False
    
    # 验证步骤3: 验证到交大的距离 > 500 米
    print("验证步骤3: 验证到交大的距离 > 500 米...")
    jiaoda_search_result = maps_text_search(jiaoda_keywords, jiaoda_city)
    if jiaoda_search_result.error:
        print(f"  验证失败: 搜索交大失败 - {jiaoda_search_result.error}")
        all_passed = False
    elif not jiaoda_search_result.pois or len(jiaoda_search_result.pois) == 0:
        print("  验证失败: 未找到交大 POI")
        all_passed = False
    else:
        jiaoda_poi_id = jiaoda_search_result.pois[0].id
        jiaoda_detail = maps_search_detail(jiaoda_poi_id)
        if jiaoda_detail.error or not jiaoda_detail.location:
            print(f"  验证失败: 无法获取交大坐标 - {jiaoda_detail.error if jiaoda_detail.error else '坐标为空'}")
            all_passed = False
        else:
            jiaoda_location = jiaoda_detail.location
            if not target_poi_location:
                print("  验证失败: 目标 POI 坐标未获取")
                all_passed = False
            else:
                distance_result = maps_distance(target_poi_location, jiaoda_location)
                if distance_result.error or not distance_result.results:
                    print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance > 500:
                        print(f"  验证通过: 距离 {distance} 米 > 500 米")
                    else:
                        print(f"  验证失败: 距离 {distance} 米 <= 500 米")
                        all_passed = False
    
    # 验证步骤4: 验证驾车路线途经点中至少有一个点距离黄雁村地铁站 < 500 米
    print("验证步骤4: 验证驾车路线途经点中至少有一个点距离黄雁村地铁站 < 500 米...")
    if not target_poi_location:
        print("  验证失败: 目标 POI 坐标未获取")
        all_passed = False
    else:
        driving_result = maps_driving_by_coordinates(user_location, target_poi_location)
        if driving_result.error or not driving_result.steps:
            print(f"  验证失败: 获取驾车路线失败 - {driving_result.error if driving_result.error else 'steps为空'}")
            all_passed = False
        else:
            found_nearby_point = False
            # 遍历steps，对from_coordinates 和 to_coordinates（不包括起点和终点）
            all_coords = set()
            for i, step in enumerate(driving_result.steps):
                # 不包括起点和终点
                if i > 0:  # from_coordinates 不是起点
                    all_coords.add(step.from_coordinates)
                if i < len(driving_result.steps) - 1:  # to_coordinates 不是终点
                    all_coords.add(step.to_coordinates)
            
            for coord in all_coords:
                distance_result = maps_distance(coord, huangyancun_station)
                if not distance_result.error and distance_result.results:
                    distance = distance_result.results[0].distance_meters
                    if distance < 500:
                        found_nearby_point = True
                        print(f"  验证通过: 找到途经点 {coord} 距离黄雁村地铁站 {distance} 米 < 500 米")
                        break
            
            if not found_nearby_point:
                print("  验证失败: 未找到距离黄雁村地铁站 < 500 米的途经点")
                all_passed = False
    
    # 验证步骤5: 验证目标 POI 到黄雁村地铁站的距离 < 200 米
    print("验证步骤5: 验证目标 POI 到黄雁村地铁站的距离 < 200 米...")
    if not target_poi_location:
        print("  验证失败: 目标 POI 坐标未获取")
        all_passed = False
    else:
        distance_result = maps_distance(target_poi_location, huangyancun_station)
        if distance_result.error or not distance_result.results:
            print(f"  验证失败: 计算距离失败 - {distance_result.error if distance_result.error else '结果为空'}")
            all_passed = False
        else:
            distance = distance_result.results[0].distance_meters
            if distance < 200:
                print(f"  验证通过: 距离 {distance} 米 < 200 米")
            else:
                print(f"  验证失败: 距离 {distance} 米 >= 200 米")
                all_passed = False
    
    # 验证步骤6: 验证总驾车时间 <= 40 分钟（2400 秒）
    print("验证步骤6: 验证总驾车时间 <= 40 分钟（2400 秒）...")
    if not target_poi_location:
        print("  验证失败: 目标 POI 坐标未获取")
        all_passed = False
    else:
        # 计算西安火车站到目标 POI 的驾车时间 t1
        route1 = maps_driving_by_coordinates(xian_train_station, target_poi_location)
        if route1.error or route1.total_duration_seconds is None:
            print(f"  验证失败: 计算西安火车站到目标 POI 的驾车时间失败 - {route1.error if route1.error else '时间为空'}")
            all_passed = False
        else:
            t1 = route1.total_duration_seconds
            # 计算目标 POI 到西安北站的驾车时间 t2
            route2 = maps_driving_by_coordinates(target_poi_location, xian_north_station)
            if route2.error or route2.total_duration_seconds is None:
                print(f"  验证失败: 计算目标 POI 到西安北站的驾车时间失败 - {route2.error if route2.error else '时间为空'}")
                all_passed = False
            else:
                t2 = route2.total_duration_seconds
                total_time = t1 + t2
                if total_time <= 2400:
                    print(f"  验证通过: 总时间 {total_time} 秒 <= 2400 秒 (t1={t1}秒, t2={t2}秒)")
                else:
                    print(f"  验证失败: 总时间 {total_time} 秒 > 2400 秒 (t1={t1}秒, t2={t2}秒)")
                    all_passed = False
    
    # 验证步骤7: 验证两个骑行时间的差值 <= 5 分钟（300 秒）
    print("验证步骤7: 验证两个骑行时间的差值 <= 5 分钟（300 秒）...")
    if not target_poi_location:
        print("  验证失败: 目标 POI 坐标未获取")
        all_passed = False
    else:
        # 计算西北工业大学到目标 POI 的骑行时间 t3
        route3 = maps_bicycling_by_coordinates(nwpu_location, target_poi_location)
        if route3.error or route3.total_duration_seconds is None:
            print(f"  验证失败: 计算西北工业大学到目标 POI 的骑行时间失败 - {route3.error if route3.error else '时间为空'}")
            all_passed = False
        else:
            t3 = route3.total_duration_seconds
            # 计算西安体育学院到目标 POI 的骑行时间 t4
            route4 = maps_bicycling_by_coordinates(xian_sport_location, target_poi_location)
            if route4.error or route4.total_duration_seconds is None:
                print(f"  验证失败: 计算西安体育学院到目标 POI 的骑行时间失败 - {route4.error if route4.error else '时间为空'}")
                all_passed = False
            else:
                t4 = route4.total_duration_seconds
                time_diff = abs(t3 - t4)
                if time_diff <= 300:
                    print(f"  验证通过: 时间差 {time_diff} 秒 <= 300 秒 (t3={t3}秒, t4={t4}秒)")
                else:
                    print(f"  验证失败: 时间差 {time_diff} 秒 > 300 秒 (t3={t3}秒, t4={t4}秒)")
                    all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")  


if __name__ == "__main__":
    main()
