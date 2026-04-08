"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（2公里内）：调用 maps_around_search(location='118.140195,24.501654', radius='2000', keywords='KTV')，验证返回pois中包含 target_poi_id='B0G2XOSQHD'。
2) 评分约束（>=4.4）：调用 maps_search_detail(id='B0G2XOSQHD')，读取 biz_ext.rating，验证 rating>=4.4。
3) 步行时间约束（<=20分钟）：从 maps_search_detail 取该POI的location='118.121823,24.505417'；调用 maps_walking_by_coordinates(origin='118.140195,24.501654', destination='118.121823,24.505417')，验证 total_duration_seconds<=1200。
4) 到高铁站驾车时间（<=30分钟）：调用 maps_geo(address='厦门北站', city='厦门') 取 location='118.073909,24.636977'；调用 maps_driving_by_coordinates(origin='118.121823,24.505417', destination='118.073909,24.636977')，验证 total_duration_seconds<=1800。
5) 到指定地铁站直线距离（<=900米）：调用 maps_geo(address='乌石浦地铁站', city='厦门') 取 location='118.126403,24.498734'；调用 maps_distance(origins='118.121823,24.505417', destination='118.126403,24.498734')，验证 distance_meters<=900。
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
    maps_walking_by_coordinates,
    maps_geo,
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.140195,24.501654",
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    search_radius: int = 2000,  # 2km
    keywords: str = "KTV",
    min_rating: float = 4.4,
    station_address: str = "厦门北站",
    station_city: str = "厦门",
    max_driving_duration: int = 1800,  # 30 minutes = 1800 seconds
    metro_station_address: str = "乌石浦地铁站",
    metro_station_city: str = "厦门",
    max_distance_meters: int = 900  # 900米
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 距离约束（2公里内）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 评分约束（>=4.4）：调用 maps_search_detail，验证 rating>=4.4。
    3) 步行时间约束（<=20分钟）：调用 maps_walking_by_coordinates，验证 total_duration_seconds<=1200。
    4) 到高铁站驾车时间（<=30分钟）：调用 maps_geo 获取厦门北站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds<=1800。
    5) 到指定地铁站直线距离（<=900米）：调用 maps_geo 获取乌石浦地铁站坐标，再调用 maps_distance，验证 distance_meters<=900。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.140195,24.501654"
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"KTV"
        min_rating: 最小评分，默认4.4
        station_address: 高铁站地址，默认"厦门北站"
        station_city: 高铁站所在城市，默认"厦门"
        max_driving_duration: 最大驾车时长（秒），默认1800（30分钟）
        metro_station_address: 地铁站地址，默认"乌石浦地铁站"
        metro_station_city: 地铁站所在城市，默认"厦门"
        max_distance_meters: 最大距离（米），默认900
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近2公里内）
    print(f"【步骤1】验证周边可达性（{search_radius}米范围内）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois or len(around_search_result.pois) == 0:
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
    
    # 步骤2: 获取目标POI详情并验证评分
    print(f"\n【步骤2】验证POI详情和评分")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location} ({poi_detail.name})")
    
    # 验证评分
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息，无法验证评分")
        return False
    
    rating = poi_detail.biz_ext.get("rating")
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_float = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析评分: {rating}")
        return False
    
    if rating_float < min_rating:
        print(f"❌ 评分{rating_float}低于要求{min_rating}")
        return False
    print(f"✅ 评分{rating_float}符合要求（>= {min_rating}）")
    
    # 步骤3: 步行时间约束（<=20分钟）
    print(f"\n【步骤3】验证从用户位置步行可达")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    
    # 步骤4: 到高铁站驾车时间（<=30分钟）
    print(f"\n【步骤4】验证到{station_address}的驾车时间")
    print("-" * 80)
    station_geo_result = maps_geo(address=station_address, city=station_city)
    if station_geo_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_geo_result.error}")
        return False
    
    if not station_geo_result.results or len(station_geo_result.results) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False
    
    station_location = station_geo_result.results[0].location
    print(f"✅ 获取{station_address}坐标: {station_location}")
    
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 步骤5: 到指定地铁站直线距离（<=900米）
    print(f"\n【步骤5】验证到{metro_station_address}的直线距离")
    print("-" * 80)
    metro_geo_result = maps_geo(address=metro_station_address, city=metro_station_city)
    if metro_geo_result.error:
        print(f"❌ 获取{metro_station_address}坐标失败: {metro_geo_result.error}")
        return False
    
    if not metro_geo_result.results or len(metro_geo_result.results) == 0:
        print(f"❌ 未找到{metro_station_address}坐标")
        return False
    
    metro_location = metro_geo_result.results[0].location
    print(f"✅ 获取{metro_station_address}坐标: {metro_location}")
    
    # 计算距离
    distance_result = maps_distance(origins=poi_location, destination=metro_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离信息")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance_meters:
        print(f"❌ 距离{metro_station_address}{distance_meters}米，超过要求{max_distance_meters}米")
        return False
    print(f"✅ 距离{metro_station_address}{distance_meters}米，符合要求（<= {max_distance_meters}米）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 531.py <poi_id> [user_location]")
        print("示例: python 531.py B0G2XOSQHD")
        print("示例: python 531.py B0G2XOSQHD 118.140195,24.501654")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0G2XOSQHD"
        user_location = "118.140195,24.501654"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "118.140195,24.501654"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
