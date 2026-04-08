"""
修改任务指令：你要找一家附近1.5km内的药店，走路过去不要超过10分钟。你还得尽快打车去海口东站，所以这家药店开车到海口东站的时间要在20分钟以内。另外你不想跑太远，药店到海口美兰国际机场开车也要在35分钟以内。为了避免去太偏的地方，你还要求这家药店在高德上的评分不低于3.7分。你说话时会夹杂英语单词，有些不耐烦。

验证方法：验证目标POI（药店）是否符合要求
目标POI ID: B0JGU1LFLU
用户位置: 110.336349,20.065149

验证步骤：
1) 周边约束：调用 maps_around_search({location: "110.336349,20.065149", radius:"1500", keywords:"药店"})，
   验证返回pois中包含目标poi_id=B0JGU1LFLU。

2) 评分约束：调用 maps_search_detail({id:"B0JGU1LFLU"})，读取 biz_ext.rating，验证评分>=3.7。

3) 步行时间约束：用 maps_search_detail 获取目标location；
   调用 maps_walking_by_coordinates({origin:"110.336349,20.065149", destination:目标location})，
   验证 total_duration_seconds<=600（10分钟）。

4) 到海口东站驾车时间约束：调用 maps_text_search(keywords="海口东站", city="海口") 拿到 poi_id，再 maps_search_detail(poi_id) 得到海口东站坐标；
   调用 maps_driving_by_coordinates({origin:目标location, destination:海口东站坐标})，
   验证 total_duration_seconds<=1200（20分钟）。

5) 到海口美兰国际机场驾车时间约束：调用 maps_text_search(keywords="海口美兰国际机场", city="海口") 拿到 poi_id，再 maps_search_detail(poi_id) 得到机场坐标；
   调用 maps_driving_by_coordinates({origin:目标location, destination:机场坐标})，
   验证 total_duration_seconds<=2100（35分钟）。
"""

import sys
import os

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_text_search,
    maps_walking_by_coordinates,
    maps_driving_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str = "B0JGU1LFLU",
    user_location: str = "110.336349,20.065149",
    search_radius: int = 1500,  # 1.5km
    keywords: str = "药店",
    min_rating: float = 3.7,  # 最低评分
    max_walking_duration: int = 600,  # 10分钟 = 600秒
    station_address: str = "海口东站",
    station_city: str = "海口",
    max_driving_to_station: int = 1200,  # 20分钟 = 1200秒
    airport_address: str = "海口美兰国际机场",
    airport_city: str = "海口",
    max_driving_to_airport: int = 2100,  # 35分钟 = 2100秒
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0JGU1LFLU"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "110.336349,20.065149"
        search_radius: 搜索半径（米），默认 1500（1.5公里）
        keywords: 搜索关键词，默认 "药店"
        min_rating: 最低评分要求，默认 3.7
        max_walking_duration: 步行最大时长（秒），默认 600（10分钟）
        station_address: 火车站地址，默认 "海口东站"
        station_city: 火车站所在城市，默认 "海口"
        max_driving_to_station: 到火车站驾车最大时长（秒），默认 1200（20分钟）
        airport_address: 机场地址，默认 "海口美兰国际机场"
        airport_city: 机场所在城市，默认 "海口"
        max_driving_to_airport: 到机场驾车最大时长（秒），默认 2100（35分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 周边约束 ====================
    print("\n【步骤1】周边约束验证（附近1.5公里内）")
    print(f"  搜索参数: location={user_location}, radius={search_radius}, keywords={keywords}")
    
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    
    if around_search_result.error:
        print(f"  ❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
        print(f"  ❌ 未找到符合条件的POI")
        return False
    
    pois_count = len(around_search_result.pois)
    print(f"  找到 {pois_count} 个{keywords}")
    
    # 验证目标POI在列表中
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"  ✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break
    
    if not poi_found:
        print(f"  ❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # ==================== 步骤2: 评分约束 ====================
    print("\n【步骤2】评分约束验证（>=3.7分）")
    print(f"  获取POI详情: id={poi_id}")
    
    poi_detail = maps_search_detail(id=poi_id)
    
    if poi_detail.error:
        print(f"  ❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    print(f"  POI名称: {poi_detail.name}")
    print(f"  POI地址: {poi_detail.address}")
    
    if not poi_detail.location:
        print(f"  ❌ POI没有location信息")
        return False
    
    target_poi_location = poi_detail.location
    print(f"  POI坐标: {target_poi_location}")
    
    # 获取评分
    rating = None
    if poi_detail.biz_ext:
        rating_str = poi_detail.biz_ext.get("rating", "")
        if rating_str:
            try:
                rating = float(rating_str)
            except (ValueError, TypeError):
                rating = None
        print(f"  POI评分: {rating_str if rating_str else '未提供'}")
    else:
        print(f"  未找到biz_ext信息")
    
    if rating is None:
        print(f"  ❌ 无法获取POI评分")
        return False
    
    if rating < min_rating:
        print(f"  ❌ POI评分 {rating} 低于要求的 {min_rating}")
        return False
    print(f"  ✅ 评分验证通过（{rating} >= {min_rating}）")
    
    # ==================== 步骤3: 步行时间约束 ====================
    print("\n【步骤3】步行时间约束验证（<=10分钟）")
    print(f"  计算步行路线: origin={user_location}, destination={target_poi_location}")
    
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if walking_result.error:
        print(f"  ❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    walking_duration_minutes = walking_duration / 60
    
    print(f"  步行时长: {walking_duration}秒（约{walking_duration_minutes:.1f}分钟）")
    
    if walking_duration > max_walking_duration:
        print(f"  ❌ 步行时长 {walking_duration}秒 超过最大限制 {max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"  ✅ 步行时间验证通过（{walking_duration}秒 <= {max_walking_duration}秒）")
    
    # ==================== 步骤4: 到海口东站驾车时间约束 ====================
    print("\n【步骤4】到海口东站驾车时间约束验证（<=20分钟）")
    print(f"  获取海口东站坐标: keywords={station_address}, city={station_city}")
    
    station_text_search_result = maps_text_search(keywords=station_address, city=station_city)
    
    if station_text_search_result.error:
        print(f"  ❌ 获取海口东站坐标失败: {station_text_search_result.error}")
        return False
    
    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"  ❌ 未找到海口东站坐标")
        return False
    
    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"  ❌ 获取海口东站详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"  ❌ 海口东站无坐标信息")
        return False
    station_location = station_detail_result.location
    station_formatted_address = station_detail_result.address or station_detail_result.name or ""
    print(f"  海口东站地址: {station_formatted_address}")
    print(f"  海口东站坐标: {station_location}")
    
    # 计算驾车时间
    print(f"  计算驾车路线: origin={target_poi_location}, destination={station_location}")
    
    driving_to_station_result = maps_driving_by_coordinates(
        origin=target_poi_location,
        destination=station_location
    )
    
    if driving_to_station_result.error:
        print(f"  ❌ 计算驾车路线失败: {driving_to_station_result.error}")
        return False
    
    if driving_to_station_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取驾车时长")
        return False
    
    driving_to_station_duration = driving_to_station_result.total_duration_seconds
    driving_to_station_minutes = driving_to_station_duration / 60
    
    print(f"  到海口东站驾车时长: {driving_to_station_duration}秒（约{driving_to_station_minutes:.1f}分钟）")
    
    if driving_to_station_duration > max_driving_to_station:
        print(f"  ❌ 驾车时长 {driving_to_station_duration}秒 超过最大限制 {max_driving_to_station}秒（{max_driving_to_station // 60}分钟）")
        return False
    print(f"  ✅ 到海口东站驾车时间验证通过（{driving_to_station_duration}秒 <= {max_driving_to_station}秒）")
    
    # ==================== 步骤5: 到海口美兰国际机场驾车时间约束 ====================
    print("\n【步骤5】到海口美兰国际机场驾车时间约束验证（<=35分钟）")
    print(f"  获取机场坐标: keywords={airport_address}, city={airport_city}")
    
    airport_text_search_result = maps_text_search(keywords=airport_address, city=airport_city)
    
    if airport_text_search_result.error:
        print(f"  ❌ 获取机场坐标失败: {airport_text_search_result.error}")
        return False
    
    if not airport_text_search_result.pois or len(airport_text_search_result.pois) == 0:
        print(f"  ❌ 未找到机场坐标")
        return False
    
    airport_poi_id = airport_text_search_result.pois[0].id
    airport_detail_result = maps_search_detail(id=airport_poi_id)
    if airport_detail_result.error:
        print(f"  ❌ 获取机场详情失败: {airport_detail_result.error}")
        return False
    if not airport_detail_result.location:
        print(f"  ❌ 机场无坐标信息")
        return False
    airport_location = airport_detail_result.location
    airport_formatted_address = airport_detail_result.address or airport_detail_result.name or ""
    print(f"  机场地址: {airport_formatted_address}")
    print(f"  机场坐标: {airport_location}")
    
    # 计算驾车时间
    print(f"  计算驾车路线: origin={target_poi_location}, destination={airport_location}")
    
    driving_to_airport_result = maps_driving_by_coordinates(
        origin=target_poi_location,
        destination=airport_location
    )
    
    if driving_to_airport_result.error:
        print(f"  ❌ 计算驾车路线失败: {driving_to_airport_result.error}")
        return False
    
    if driving_to_airport_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取驾车时长")
        return False
    
    driving_to_airport_duration = driving_to_airport_result.total_duration_seconds
    driving_to_airport_minutes = driving_to_airport_duration / 60
    
    print(f"  到机场驾车时长: {driving_to_airport_duration}秒（约{driving_to_airport_minutes:.1f}分钟）")
    
    if driving_to_airport_duration > max_driving_to_airport:
        print(f"  ❌ 驾车时长 {driving_to_airport_duration}秒 超过最大限制 {max_driving_to_airport}秒（{max_driving_to_airport // 60}分钟）")
        return False
    print(f"  ✅ 到机场驾车时间验证通过（{driving_to_airport_duration}秒 <= {max_driving_to_airport}秒）")
    
    # ==================== 所有验证通过 ====================
    print("\n" + "=" * 60)
    print("✅ 所有验证通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # 执行验证
    result = verify_poi()
    print(f"\n最终验证结果: {'通过 ✅' if result else '失败 ❌'}")
    sys.exit(0 if result else 1)
