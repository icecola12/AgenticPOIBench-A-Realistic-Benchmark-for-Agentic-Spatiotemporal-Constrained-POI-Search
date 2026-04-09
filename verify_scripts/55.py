"""
修改任务指令：你想找一家附近2公里内的餐厅，打算先去那里把合同打印出来并跟客户见面。餐厅走路过去要在15分钟以内。你也要考虑客户从金华站打车过来，餐厅开车到金华站不能超过12分钟。为了不耽误后面的行程，这家餐厅必须是24小时营业的。口碑也要过得去，评分至少4.1分。你一个喜欢开玩笑的有趣的人，试图让对话变得轻松。

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(附近2公里内)：用 maps_around_search 以用户坐标(119.664619,29.064864)为中心、radius=2000、keywords=餐厅 搜索，验证返回pois中包含目标poi_id=B0H2H1L9Z9。  
2) 步行15分钟内：先用 maps_search_detail(B0H2H1L9Z9) 取目标POI坐标destination；再用 maps_walking_by_coordinates(origin=119.664619,29.064864, destination=POI坐标) 得到 total_duration_seconds，验证 <= 900。  
3) 客户从金华站打车到店、且不超过12分钟：用 maps_search_detail(B02430I2WW) 获取金华站坐标；用 maps_driving_by_coordinates(origin=目标POI坐标, destination=金华站坐标) 得到 total_duration_seconds，验证 <= 720。  
4) 24小时营业：用 maps_search_detail(B0H2H1L9Z9) 读取 biz_ext.opentime2 或 biz_ext.open_time，验证包含"00:00-24:00"或"24小时营业"。  
5) 评分至少4.1：用 maps_search_detail(B0H2H1L9Z9) 读取 biz_ext.rating，验证数值 >= 4.1。
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
    maps_driving_by_coordinates,
)
from tools.amap_tools import maps_around_search


def check_24_hours_business(biz_ext: dict) -> bool:
    """
    检查是否为24小时营业
    
    Args:
        biz_ext: POI的biz_ext字典
    
    Returns:
        bool: True表示是24小时营业，False表示不是或无法确定
    """
    if not biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 尝试读取open_time或opentime2
    opentime_str = None
    if biz_ext.get("opentime2"):
        opentime_str = biz_ext.get("opentime2")
        print(f"📅 找到opentime2: {opentime_str}")
    elif biz_ext.get("open_time"):
        opentime_str = biz_ext.get("open_time")
        print(f"📅 找到open_time: {opentime_str}")
    
    if not opentime_str:
        print(f"❌ 无法找到营业时间信息（open_time/opentime2）")
        return False
    
    # 检查各种24小时营业的表示方式
    time_str_lower = opentime_str.lower()
    is_24h = (
        "24小时" in opentime_str or
        "全天" in opentime_str or
        "00:00-24:00" in opentime_str or
        "00:00-00:00" in opentime_str or
        "24h" in time_str_lower
    )
    
    if is_24h:
        print(f"✅ 通过: 24小时营业 ({opentime_str})")
        return True
    else:
        print(f"❌ 未通过: 不是24小时营业 (营业时间: {opentime_str})")
        return False


def verify_poi(
    poi_id: str,
    user_location: str = "119.664619,29.064864",
    restaurant_location: str = None,
    search_radius: int = 2000,
    keywords: str = "餐厅",
    max_walking_duration: int = 900,  # 15分钟 = 900秒
    station_poi_id: str = "B02430I2WW",
    station_location: str = None,
    max_driving_duration: int = 720,  # 12分钟 = 720秒
    min_rating: float = 4.1
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 距离约束(附近2公里内)：用 maps_around_search 搜索，验证返回pois中包含目标poi_id。
    2) 步行15分钟内：先用 maps_search_detail 取目标POI坐标；再用 maps_walking_by_coordinates 得到 total_duration_seconds，验证 <= 900。
    3) 客户从金华站打车到店、且不超过12分钟：用 maps_search_detail 获取金华站坐标；用 maps_driving_by_coordinates 得到 total_duration_seconds，验证 <= 720。
    4) 24小时营业：用 maps_search_detail 读取 biz_ext.opentime2 或 biz_ext.open_time，验证包含"00:00-24:00"或"24小时营业"。
    5) 评分至少4.1：用 maps_search_detail 读取 biz_ext.rating，验证数值 >= 4.1。
    
    Args:
        poi_id: POI ID，默认"B0H2H1L9Z9"
        user_location: 用户坐标，格式为"经度,纬度"，默认"119.664619,29.064864"
        restaurant_location: 餐厅坐标，格式为"经度,纬度"，如果为None则从POI详情中获取
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"餐厅"
        max_walking_duration: 最大步行时长（秒），默认900（15分钟）
        station_poi_id: 火车站POI ID，默认"B02430I2WW"
        station_location: 火车站坐标，格式为"经度,纬度"，如果为None则从maps_search_detail获取
        max_driving_duration: 最大驾车时长（秒），默认720（12分钟）
        min_rating: 最小评分，默认4.1
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束(附近2公里内)
    print(f"【步骤1】验证距离约束（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
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
    
    # 步骤2: 获取目标POI坐标并验证步行15分钟内
    print(f"\n【步骤2】获取目标POI坐标并验证步行时长限制（<={max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    print("-" * 80)
    restaurant_detail = maps_search_detail(id=poi_id)
    if restaurant_detail.error:
        print(f"❌ 获取餐厅详情失败: {restaurant_detail.error}")
        return False
    
    if restaurant_detail.location:
        restaurant_location = restaurant_detail.location
        print(f"✅ 获取餐厅坐标: {restaurant_location} ({restaurant_detail.name})")
    else:
        if restaurant_location is None:
            print(f"❌ POI没有location信息")
            return False
        print(f"⚠️  餐厅详情中没有location信息，使用传入的默认坐标: {restaurant_location}")
    
    # 验证步行时长
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=restaurant_location
    )
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
    
    # 步骤3: 客户从金华站打车到店、且不超过12分钟
    print(f"\n【步骤3】验证餐厅到金华站驾车时长限制（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    # 3.1 获取金华站坐标
    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取火车站详情失败: {station_detail.error}")
        return False
    
    if station_detail.location:
        station_location = station_detail.location
        print(f"✅ 获取火车站坐标: {station_location} ({station_detail.name})")
    else:
        if station_location is None:
            print(f"❌ 火车站没有location信息")
            return False
        print(f"⚠️  火车站详情中没有location信息，使用传入的默认坐标: {station_location}")
    
    # 3.2 计算驾车时间（从餐厅到金华站）
    driving_result = maps_driving_by_coordinates(
        origin=restaurant_location,
        destination=station_location
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 步骤4: 24小时营业验证
    print(f"\n【步骤4】验证24小时营业")
    print("-" * 80)
    if not restaurant_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    if not check_24_hours_business(restaurant_detail.biz_ext):
        return False
    
    # 步骤5: 评分至少4.1验证
    print(f"\n【步骤5】验证评分约束（>={min_rating}）")
    print("-" * 80)
    rating = restaurant_detail.biz_ext.get("rating")
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
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 612.py <poi_id> [user_location] [restaurant_location]")
        print("示例: python 612.py B0H2H1L9Z9")
        print("示例: python 612.py B0H2H1L9Z9 119.664619,29.064864")
        print("示例: python 612.py B0H2H1L9Z9 119.664619,29.064864 119.664619,29.064864")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0H2H1L9Z9"
        user_location = "119.664619,29.064864"
        restaurant_location = "119.664619,29.064864"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "119.664619,29.064864"
        restaurant_location = sys.argv[3] if len(sys.argv) > 3 else None
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    if restaurant_location:
        print(f"餐厅坐标: {restaurant_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, restaurant_location=restaurant_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
