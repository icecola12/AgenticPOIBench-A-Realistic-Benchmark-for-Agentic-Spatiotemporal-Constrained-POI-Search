"""修改任务指令：你想找一家附近2公里内的咖啡厅，骑车过去全程不要超过1公里。为了等会儿方便接待客户，这家咖啡厅走路过去也必须在12分钟内能到。你还希望这家店今天在22:00之后还在营业。另外，为了办完事顺路逛一下，咖啡厅300米范围内要有购物中心。你依赖心强，希望智能体能为自己处理和决定一切。

验证方法：验证目标POI（咖啡厅）是否符合要求
目标POI ID: B0JAXS6I6M
用户位置: 113.411472,23.10479
用户地址: 广东省广州市天河区前进街道黄埔大道东732号
执行时间: 周二 21:10:00

验证步骤：
1) 调用 maps_around_search(location=用户坐标, radius=2000, keywords=咖啡厅)，
   验证返回pois数量>=8，且目标poi_id在pois列表中（满足"2公里内咖啡厅"）。

2) 调用 maps_search_detail(id=目标poi_id)，获取目标POI的location与biz_ext.open_time/opentime2。

3) 调用 maps_walking_by_coordinates(origin=用户坐标, destination=POI.location)，
   验证 total_duration_seconds <= 12*60（满足"步行12分钟内"）。

4) 调用 maps_bicycling_by_coordinates(origin=用户坐标, destination=POI.location)，
   验证 total_distance_meters <= 1000（满足"骑行不超过1公里"）。

5) 结合第2步返回的 open_time 或 opentime2，验证该POI在22:00之后仍营业：
   即营业结束时间晚于22:00（满足"22:00后仍营业"）。

6) 调用 maps_around_search(location=POI.location, radius=300, keywords=购物中心)，
   验证返回pois列表非空（满足"300米内有购物中心"）。
"""

import sys
import os
import re

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates,
)
from tools.amap_tools import maps_around_search


def parse_closing_time(open_time_str: str) -> int:
    """
    解析营业时间字符串，提取结束时间（小时数）
    
    Args:
        open_time_str: 营业时间字符串，如 "07:00-22:30" 或 "08:00-23:00"
    
    Returns:
        结束时间的小时数（如 22:30 返回 22），如果无法解析返回 -1
    """
    if not open_time_str:
        return -1
    
    # 匹配常见的营业时间格式：HH:MM-HH:MM
    match = re.search(r'(\d{1,2}):(\d{2})\s*[-~]\s*(\d{1,2}):(\d{2})', open_time_str)
    if match:
        start_hour = int(match.group(1))
        start_minute = int(match.group(2))
        end_hour = int(match.group(3))
        end_minute = int(match.group(4))
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute
        # 跨天（如 10:00-2:00）：有效关门在次日，返回 end_minutes + 24*60 便于与阈值比较
        if end_minutes < start_minutes:
            return end_minutes + 24 * 60
        return end_minutes
    
    # 处理24小时营业的情况
    if "24小时" in open_time_str or "全天" in open_time_str:
        return 24 * 60  # 返回24:00
    
    return -1


def verify_poi(
    poi_id: str = "B0JAXS6I6M",
    user_location: str = "113.411472,23.10479",
    search_radius: int = 2000,  # 2km
    keywords: str = "咖啡厅",
    min_pois_count: int = 8,  # 最少POI数量
    max_walking_duration: int = 720,  # 12分钟 = 720秒
    max_bicycling_distance: int = 1000,  # 骑行最大距离1000米
    min_closing_time: int = 22 * 60,  # 22:00 = 1320分钟
    shopping_center_radius: int = 300,  # 购物中心搜索半径300米
    shopping_center_keywords: str = "购物中心",
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0JAXS6I6M"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "113.411472,23.10479"
        search_radius: 搜索半径（米），默认 2000（2公里）
        keywords: 搜索关键词，默认 "咖啡厅"
        min_pois_count: 最少POI数量，默认 8
        max_walking_duration: 步行最大时长（秒），默认 720（12分钟）
        max_bicycling_distance: 骑行最大距离（米），默认 1000
        min_closing_time: 最晚营业结束时间（分钟数），默认 22*60（22:00）
        shopping_center_radius: 购物中心搜索半径（米），默认 300
        shopping_center_keywords: 购物中心搜索关键词，默认 "购物中心"
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 周边搜索验证 ====================
    print("\n【步骤1】周边搜索验证（2公里内咖啡厅，数量>=8）")
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
    
    # 验证POI数量 >= 8
    if pois_count < min_pois_count:
        print(f"  ❌ POI数量 {pois_count} 少于要求的 {min_pois_count} 个")
        return False
    print(f"  ✅ POI数量验证通过（{pois_count} >= {min_pois_count}）")
    
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
    
    # ==================== 步骤2: 获取POI详情 ====================
    print("\n【步骤2】获取POI详情")
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
    
    # 获取营业时间
    open_time = ""
    opentime2 = ""
    if poi_detail.biz_ext:
        open_time = poi_detail.biz_ext.get("open_time", "")
        opentime2 = poi_detail.biz_ext.get("opentime2", "")
        print(f"  营业时间 (open_time): {open_time if open_time else '未提供'}")
        print(f"  营业时间 (opentime2): {opentime2 if opentime2 else '未提供'}")
    else:
        print(f"  未找到biz_ext信息")
    
    # ==================== 步骤3: 步行时间验证 ====================
    print("\n【步骤3】步行时间验证（<=12分钟）")
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
    
    # ==================== 步骤4: 骑行距离验证 ====================
    print("\n【步骤4】骑行距离验证（<=1公里）")
    print(f"  计算骑行路线: origin={user_location}, destination={target_poi_location}")
    
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if bicycling_result.error:
        print(f"  ❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_distance_meters is None:
        print(f"  ❌ 无法获取骑行距离")
        return False
    
    bicycling_distance = bicycling_result.total_distance_meters
    bicycling_distance_km = bicycling_distance / 1000
    
    print(f"  骑行距离: {bicycling_distance}米（{bicycling_distance_km:.2f}公里）")
    
    if bicycling_distance > max_bicycling_distance:
        print(f"  ❌ 骑行距离 {bicycling_distance}米 超过最大限制 {max_bicycling_distance}米（{max_bicycling_distance / 1000}公里）")
        return False
    print(f"  ✅ 骑行距离验证通过（{bicycling_distance}米 <= {max_bicycling_distance}米）")
    
    # ==================== 步骤5: 营业时间验证（22:00后仍营业） ====================
    print("\n【步骤5】营业时间验证（22:00后仍营业）")
    
    # 尝试从 open_time 和 opentime2 解析结束时间
    closing_time_minutes = parse_closing_time(open_time)
    if closing_time_minutes < 0:
        closing_time_minutes = parse_closing_time(opentime2)
    
    if closing_time_minutes < 0:
        print(f"  ❌ 无法解析营业时间")
        return False
    
    closing_hour = closing_time_minutes // 60
    closing_minute = closing_time_minutes % 60
    print(f"  营业结束时间: {closing_hour:02d}:{closing_minute:02d}")
    
    if closing_time_minutes < min_closing_time:
        min_hour = min_closing_time // 60
        min_minute = min_closing_time % 60
        print(f"  ❌ 营业结束时间 {closing_hour:02d}:{closing_minute:02d} 早于要求的 {min_hour:02d}:{min_minute:02d}")
        return False
    print(f"  ✅ 营业时间验证通过（结束时间 {closing_hour:02d}:{closing_minute:02d} >= 22:00）")
    
    # ==================== 步骤6: 购物中心近邻验证 ====================
    print("\n【步骤6】购物中心近邻验证（300米内有购物中心）")
    print(f"  搜索参数: location={target_poi_location}, radius={shopping_center_radius}, keywords={shopping_center_keywords}")
    
    shopping_center_search_result = maps_around_search(
        location=target_poi_location,
        radius=str(shopping_center_radius),
        keywords=shopping_center_keywords
    )
    
    if shopping_center_search_result.error:
        print(f"  ❌ 搜索周边购物中心失败: {shopping_center_search_result.error}")
        return False
    
    if not shopping_center_search_result.pois or len(shopping_center_search_result.pois) == 0:
        print(f"  ❌ {shopping_center_radius}米内未找到购物中心")
        return False
    
    shopping_center_count = len(shopping_center_search_result.pois)
    first_shopping_center = shopping_center_search_result.pois[0]
    print(f"  找到 {shopping_center_count} 个购物中心")
    print(f"  最近的购物中心: {first_shopping_center.name}")
    print(f"  ✅ 购物中心近邻验证通过（{shopping_center_radius}米内有 {shopping_center_count} 个购物中心）")
    
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
