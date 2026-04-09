"""
修改任务指令：你要在附近2000米以内找一家酒店。酒店评分要在4.6分及以上。你打算第二天从天津滨海国际机场出发，所以从酒店开车去机场的时间不能超过27分钟。你还希望酒店到你这里开车不超过4公里。为了方便出门坐公共交通，酒店到周边1200米范围内的地铁站里，走到最近一个地铁站的时间要在16分钟以内。另外你需要酒店离"环湖东路(公交站)"的直线距离不超过4000米。你说话非常有条理和注重细节
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米：调用 maps_around_search(location='117.205441,39.055306', radius='2000', keywords='酒店')，验证返回pois中包含 target_poi_id='B0FFFP9NQD'。  
2) 评分≥4.6：调用 maps_search_detail(id='B0FFFP9NQD')，取 biz_ext.rating，验证 rating >= 4.6。  
3) 酒店到用户位置驾车距离≤4公里：调用 maps_driving_by_coordinates(origin='117.205441,39.055306', destination=POI.location)，验证 total_distance_meters <= 4000。  
4) 酒店到机场驾车时间≤27分钟：调用 maps_geo(address='天津滨海国际机场', city='天津') 得到机场坐标；再调用 maps_driving_by_coordinates(origin=POI.location, destination=机场坐标)，验证 total_duration_seconds <= 1620。  
5) 酒店到周边1200米内地铁站的最小步行时间≤16分钟：调用 maps_around_search(location=POI.location, radius='1200', keywords='地铁站') 获取站点集合；对集合中每个站点调用 maps_walking_by_coordinates(origin=POI.location, destination=站点.location)，取最小 total_duration_seconds，验证 <= 960。  
6) 酒店到"环湖东路(公交站)"直线距离≤4000米：调用 maps_geo(address='环湖东路(公交站)', city='天津') 得到站点坐标；再调用 maps_distance(origins=POI.location, destination=站点坐标)，验证 distance_meters <= 4000。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_driving_by_coordinates,
    maps_geo,
    maps_distance,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.205441,39.055306",
    search_radius: int = 2000,
    keywords: str = "酒店",
    min_rating: float = 4.6,
    max_driving_distance: int = 4000,  # 4公里 = 4000米
    max_driving_duration: int = 1620,  # 27分钟 = 1620秒
    subway_search_radius: int = 1200,
    subway_keywords: str = "地铁站",
    max_walking_duration: int = 960,  # 16分钟 = 960秒
    bus_station_address: str = "环湖东路(公交站)",
    bus_station_city: str = "天津",
    max_straight_distance: int = 4000,  # 4000米
    airport_address: str = "天津滨海国际机场",
    airport_city: str = "天津"
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 附近2000米：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 评分≥4.6：调用 maps_search_detail，读取 biz_ext.rating，验证 rating >= 4.6。
    3) 酒店到用户位置驾车距离≤4公里：调用 maps_driving_by_coordinates，验证 total_distance_meters <= 4000。
    4) 酒店到机场驾车时间≤27分钟：调用 maps_geo 获取机场坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 1620。
    5) 酒店到周边1200米内地铁站的最小步行时间≤16分钟：调用 maps_around_search 获取站点集合，对每个站点调用 maps_walking_by_coordinates，取最小 total_duration_seconds，验证 <= 960。
    6) 酒店到"环湖东路(公交站)"直线距离≤4000米：调用 maps_geo 得到站点坐标，再调用 maps_distance，验证 distance_meters <= 4000。
    
    Args:
        poi_id: POI ID，默认"B0FFFP9NQD"
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.205441,39.055306"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最小评分，默认4.6
        max_driving_distance: 最大驾车距离（米），默认4000（4公里）
        max_driving_duration: 最大驾车时长（秒），默认1620（27分钟）
        subway_search_radius: 地铁站搜索半径（米），默认1200
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration: 最大步行时长（秒），默认960（16分钟）
        bus_station_address: 公交站地址，默认"环湖东路(公交站)"
        bus_station_city: 公交站所在城市，默认"天津"
        max_straight_distance: 最大直线距离（米），默认4000
        airport_address: 机场地址，默认"天津滨海国际机场"
        airport_city: 机场所在城市，默认"天津"
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2000米范围验证
    # 注意：首个约束应该为"你想找一个附近指定距离的poi点"，而非"你想找一个离你不超过指定距离的poi点"
    print(f"【步骤1】验证附近范围（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索附近POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False
    
    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break
    
    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # 步骤2: 评分验证
    print(f"\n【步骤2】验证评分（>={min_rating}分）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    rating = poi_detail.biz_ext.get("rating")
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False
    
    if rating_value < min_rating:
        print(f"❌ POI评分{rating_value}，低于要求的最小评分{min_rating}")
        return False
    print(f"✅ POI评分{rating_value}，满足要求（>={min_rating}）")
    
    # 获取酒店坐标（如果详情中有location，使用详情中的；否则需要从around_search结果中获取）
    if poi_detail.location:
        hotel_location = poi_detail.location
        print(f"✅ 获取酒店坐标: {hotel_location} ({poi_detail.name})")
    else:
        # 从around_search结果中获取坐标
        hotel_location = None
        for poi in around_search_result.pois:
            if poi.id == poi_id:
                hotel_location = poi.location
                print(f"✅ 从搜索结果获取酒店坐标: {hotel_location} ({poi.name})")
                break
        
        if not hotel_location:
            print(f"❌ 无法获取酒店坐标")
            return False
    
    # 步骤3: 酒店到用户位置驾车距离验证
    print(f"\n【步骤3】验证酒店到用户位置驾车距离（<={max_driving_distance}米，即{max_driving_distance // 1000}公里）")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=hotel_location
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False
    
    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米（{max_driving_distance // 1000}公里）")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米，即{max_driving_distance // 1000}公里）")
    
    # 步骤4: 酒店到机场驾车时间验证
    print(f"\n【步骤4】验证酒店到机场驾车时间（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    # 获取机场坐标
    airport_geo_result = maps_geo(address=airport_address, city=airport_city)
    if airport_geo_result.error:
        print(f"❌ 获取机场坐标失败: {airport_geo_result.error}")
        return False
    
    if not airport_geo_result.results or len(airport_geo_result.results) == 0:
        print(f"❌ 未找到机场地址")
        return False
    
    airport_location = airport_geo_result.results[0].location
    print(f"✅ 获取机场坐标: {airport_location} ({airport_geo_result.results[0].formatted_address})")
    
    # 计算驾车时间
    airport_driving_result = maps_driving_by_coordinates(
        origin=hotel_location,
        destination=airport_location
    )
    if airport_driving_result.error:
        print(f"❌ 计算到机场驾车路线失败: {airport_driving_result.error}")
        return False
    
    if airport_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到机场的驾车时长")
        return False
    
    airport_driving_duration = airport_driving_result.total_duration_seconds
    if airport_driving_duration > max_driving_duration:
        print(f"❌ 到机场驾车时长{airport_driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到机场驾车时长{airport_driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 步骤5: 酒店到周边1200米内地铁站的最小步行时间验证
    print(f"\n【步骤5】验证酒店到周边{subway_search_radius}米内地铁站的最小步行时间（<={max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    print("-" * 80)
    subway_search_result = maps_around_search(
        location=hotel_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False
    
    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False
    
    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")
    
    # 对每个地铁站计算步行时间，取最小值
    min_walking_duration = None
    for subway_station in subway_search_result.pois:
        walking_result = maps_walking_by_coordinates(
            origin=hotel_location,
            destination=subway_station.location
        )
        if walking_result.error:
            print(f"⚠️  计算到地铁站{subway_station.name}的步行路线失败: {walking_result.error}")
            continue
        
        if walking_result.total_duration_seconds is None:
            print(f"⚠️  无法获取到地铁站{subway_station.name}的步行时长")
            continue
        
        walking_duration = walking_result.total_duration_seconds
        if min_walking_duration is None or walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            print(f"  到地铁站{subway_station.name}的步行时长: {walking_duration}秒")
    
    if min_walking_duration is None:
        print(f"❌ 无法计算到任何地铁站的步行时长")
        return False
    
    if min_walking_duration > max_walking_duration:
        print(f"❌ 最小步行时长{min_walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 最小步行时长{min_walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    
    # 步骤6: 酒店到"环湖东路(公交站)"直线距离验证
    print(f"\n【步骤6】验证酒店到\"{bus_station_address}\"直线距离（<={max_straight_distance}米）")
    print("-" * 80)
    # 获取公交站坐标
    bus_station_geo_result = maps_geo(address=bus_station_address, city=bus_station_city)
    if bus_station_geo_result.error:
        print(f"❌ 获取公交站坐标失败: {bus_station_geo_result.error}")
        return False
    
    if not bus_station_geo_result.results or len(bus_station_geo_result.results) == 0:
        print(f"❌ 未找到公交站地址")
        return False
    
    bus_station_location = bus_station_geo_result.results[0].location
    print(f"✅ 获取公交站坐标: {bus_station_location} ({bus_station_geo_result.results[0].formatted_address})")
    
    # 计算直线距离
    distance_result = maps_distance(
        origins=hotel_location,
        destination=bus_station_location
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离测量结果")
        return False
    
    straight_distance = distance_result.results[0].distance_meters
    if straight_distance > max_straight_distance:
        print(f"❌ 直线距离{straight_distance}米，超过{max_straight_distance}米")
        return False
    print(f"✅ 直线距离{straight_distance}米，符合要求（<= {max_straight_distance}米）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 754.py <poi_id> [user_location]")
        print("示例: python 754.py B0FFFP9NQD")
        print("示例: python 754.py B0FFFP9NQD 117.205441,39.055306")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0FFFP9NQD"
        user_location = "117.205441,39.055306"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "117.205441,39.055306"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
