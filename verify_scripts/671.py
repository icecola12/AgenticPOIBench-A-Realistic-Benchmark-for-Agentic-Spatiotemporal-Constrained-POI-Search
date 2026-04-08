"""
修改任务指令：你要找一家附近1200米内的超市，买完东西还得尽快去赶高铁。这个超市开车到宝鸡南站的时间要在25分钟以内，而且你希望步行过去不要超过8分钟。另外你需要它离“清姜路公交站”直线距离不超过600米，并且这家店的评分要在3.0分以上。你说话简短急促，希望快速完成所有事。

验证任务说明：
验证目标POI（超市）是否符合以下要求：

目标POI ID: B0K37SJN7T
用户位置: 107.130026,34.353819

验证步骤：
1) 距离约束（附近1200米）：调用 maps_around_search(location="107.130026,34.353819", radius="1200", keywords="超市")，
   验证返回pois中包含 target_poi_id=B0K37SJN7T。

2) 评分约束（>=3.0）：调用 maps_search_detail(id="B0K37SJN7T")，读取 biz_ext.rating，验证 rating>=3.0（该POI返回rating=3.5）。

3) 到宝鸡南站驾车时间（<=25分钟）：调用 maps_text_search(keywords="宝鸡南站", city="宝鸡") 拿到 poi_id，再 maps_search_detail(poi_id) 获取宝鸡南站坐标；
   再调用 maps_driving_by_coordinates(origin="107.129673,34.352921", destination=宝鸡南站坐标) 获取驾车时长，
   验证 total_duration_seconds/60<=25（实际约23.08分钟）。

4) 从用户位置步行时间（<=8分钟）：调用 maps_walking_by_coordinates(origin="107.130026,34.353819", destination="107.129673,34.352921")，
   验证 total_duration_seconds/60<=8（实际约5.52分钟）。

5) 到清姜路公交站直线距离（<=600米）：调用 maps_text_search(keywords="清姜路公交站", city="宝鸡") 拿到 poi_id，再 maps_search_detail(poi_id) 取其坐标；
   再调用 maps_distance(origins="107.129673,34.352921", destination=公交站坐标)，验证 distance_meters<=600（实际563米）。
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
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str = "B0K37SJN7T",
    user_location: str = "107.130026,34.353819",
    poi_location: str = "107.129673,34.352921",  # 目标POI坐标
    search_radius: int = 1200,  # 1200米
    keywords: str = "超市",
    min_rating: float = 3.0,  # 最低评分
    max_driving_duration_minutes: float = 25,  # 到宝鸡南站驾车最大时间25分钟
    max_walking_duration_minutes: float = 8,  # 用户位置步行到POI最大时间8分钟
    max_bus_stop_distance: int = 600,  # 到公交站直线距离最大600米
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0K37SJN7T"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "107.130026,34.353819"
        poi_location: 目标POI坐标，格式为"经度,纬度"，默认 "107.129673,34.352921"
        search_radius: 搜索半径（米），默认 1200
        keywords: 搜索关键词，默认 "超市"
        min_rating: 最低评分要求，默认 3.0
        max_driving_duration_minutes: 到宝鸡南站驾车最大时间（分钟），默认 25
        max_walking_duration_minutes: 用户位置步行到POI最大时间（分钟），默认 8
        max_bus_stop_distance: 到清姜路公交站直线距离（米），默认 600
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print(f"目标POI坐标: {poi_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 距离约束（附近1200米） ====================
    print("\n【步骤1】距离约束验证（附近1200米内）")
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
    
    # ==================== 步骤2: 评分约束（>=3.0） ====================
    print("\n【步骤2】评分约束验证（>=3.0分）")
    print(f"  获取POI详情: id={poi_id}")
    
    poi_detail = maps_search_detail(id=poi_id)
    
    if poi_detail.error:
        print(f"  ❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    print(f"  POI名称: {poi_detail.name}")
    print(f"  POI地址: {poi_detail.address}")
    print(f"  POI坐标: {poi_detail.location}")
    
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
    
    # ==================== 步骤3: 到宝鸡南站驾车时间（<=25分钟） ====================
    print("\n【步骤3】到宝鸡南站驾车时间验证（<=25分钟）")
    print(f"  获取宝鸡南站坐标: keywords='宝鸡南站', city='宝鸡'")
    
    text_search_result = maps_text_search(keywords="宝鸡南站", city="宝鸡")
    
    if text_search_result.error:
        print(f"  ❌ 获取宝鸡南站坐标失败: {text_search_result.error}")
        return False
    
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"  ❌ 未找到宝鸡南站坐标")
        return False
    
    station_poi_id = text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"  ❌ 获取宝鸡南站详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"  ❌ 宝鸡南站无坐标信息")
        return False
    baoji_south_station_location = station_detail_result.location
    print(f"  宝鸡南站坐标: {baoji_south_station_location}")
    
    # 计算驾车时间
    print(f"  计算驾车路线: origin={poi_location}, destination={baoji_south_station_location}")
    
    driving_result = maps_driving_by_coordinates(
        origin=poi_location,
        destination=baoji_south_station_location
    )
    
    if driving_result.error:
        print(f"  ❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取驾车时长")
        return False
    
    driving_duration_seconds = driving_result.total_duration_seconds
    driving_duration_minutes = driving_duration_seconds / 60
    
    print(f"  驾车时长: {driving_duration_seconds}秒（约{driving_duration_minutes:.2f}分钟）")
    
    if driving_duration_minutes > max_driving_duration_minutes:
        print(f"  ❌ 驾车时长 {driving_duration_minutes:.2f}分钟 超过最大限制 {max_driving_duration_minutes}分钟")
        return False
    print(f"  ✅ 驾车时间验证通过（{driving_duration_minutes:.2f}分钟 <= {max_driving_duration_minutes}分钟）")
    
    # ==================== 步骤4: 从用户位置步行时间（<=8分钟） ====================
    print("\n【步骤4】从用户位置步行时间验证（<=8分钟）")
    print(f"  计算步行路线: origin={user_location}, destination={poi_location}")
    
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    
    if walking_result.error:
        print(f"  ❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取步行时长")
        return False
    
    walking_duration_seconds = walking_result.total_duration_seconds
    walking_duration_minutes = walking_duration_seconds / 60
    
    print(f"  步行时长: {walking_duration_seconds}秒（约{walking_duration_minutes:.2f}分钟）")
    
    if walking_duration_minutes > max_walking_duration_minutes:
        print(f"  ❌ 步行时长 {walking_duration_minutes:.2f}分钟 超过最大限制 {max_walking_duration_minutes}分钟")
        return False
    print(f"  ✅ 步行时间验证通过（{walking_duration_minutes:.2f}分钟 <= {max_walking_duration_minutes}分钟）")
    
    # ==================== 步骤5: 到清姜路公交站直线距离（<=600米） ====================
    print("\n【步骤5】到清姜路公交站直线距离验证（<=600米）")
    print(f"  获取清姜路公交站坐标: keywords='清姜路公交站', city='宝鸡'")
    
    bus_stop_text_search_result = maps_text_search(keywords="清姜路公交站", city="宝鸡")
    
    if bus_stop_text_search_result.error:
        print(f"  ❌ 获取清姜路公交站坐标失败: {bus_stop_text_search_result.error}")
        return False
    
    if not bus_stop_text_search_result.pois or len(bus_stop_text_search_result.pois) == 0:
        print(f"  ❌ 未找到清姜路公交站坐标")
        return False
    
    bus_stop_poi_id = bus_stop_text_search_result.pois[0].id
    bus_stop_detail_result = maps_search_detail(id=bus_stop_poi_id)
    if bus_stop_detail_result.error:
        print(f"  ❌ 获取清姜路公交站详情失败: {bus_stop_detail_result.error}")
        return False
    if not bus_stop_detail_result.location:
        print(f"  ❌ 清姜路公交站无坐标信息")
        return False
    bus_stop_location = bus_stop_detail_result.location
    print(f"  清姜路公交站坐标: {bus_stop_location}")
    
    # 计算直线距离
    print(f"  计算直线距离: origins={poi_location}, destination={bus_stop_location}")
    
    distance_result = maps_distance(
        origins=poi_location,
        destination=bus_stop_location
    )
    
    if distance_result.error:
        print(f"  ❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"  ❌ 未找到距离结果")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    print(f"  直线距离: {distance_meters}米")
    
    if distance_meters > max_bus_stop_distance:
        print(f"  ❌ 距离 {distance_meters}米 超过最大限制 {max_bus_stop_distance}米")
        return False
    print(f"  ✅ 距离验证通过（{distance_meters}米 <= {max_bus_stop_distance}米）")
    
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
