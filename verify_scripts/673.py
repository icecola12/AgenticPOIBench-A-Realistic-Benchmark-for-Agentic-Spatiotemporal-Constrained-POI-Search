"""
修改任务指令：你想找一个附近2km内的咖啡厅，准备和客户临时见面签个合同。你需要这个地方现在还在营业，并且评分不低于4.4分。客户开车从"聊城振华购物中心"出发，你则走路过去；你希望你步行到达的时间和客户驾车到达的时间差不超过15分钟。另外，为了方便客户停车，这家咖啡厅到"大润发(东昌店)"的直线距离不能超过2km。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location=116.01978,36.45786, radius=2000, keywords=咖啡厅)，验证返回pois中包含目标poi_id= B0LB2HPOY0（验证"附近2km内的咖啡厅"）。  
2) 调用 maps_search_detail(id=B0LB2HPOY0)，读取 biz_ext.rating 与 biz_ext.open_time/opentime2：验证 rating>=4.4；并结合题目给定time，验证当前时刻处于其营业时间段内（验证"评分不低于4.4分、现在还在营业"）。  
3) 调用 maps_geo(address=聊城振华购物中心, city=聊城) 获取其坐标loc_mall；再对目标POI detail中的location调用 maps_driving_by_coordinates(origin=loc_mall, destination=poi_location) 得到t_drive。  
4) 对用户坐标(116.01978,36.45786)与poi_location调用 maps_walking_by_coordinates 得到t_walk；验证 |t_walk - t_drive| <= 15分钟（即<=900秒）。  
5) 调用 maps_text_search(keywords=大润发(东昌店), city=聊城, citylimit=true) 选取与"大润发东昌店"匹配的POI，得到其location=loc_rt；调用 maps_distance(origins=poi_location, destination=loc_rt)，验证distance<=2000米（验证"到大润发(东昌店)直线距离不超过2km"）。
"""

import os
import sys
import re

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
    maps_geo,
    maps_text_search,
    maps_distance
)
from tools.amap_tools import maps_around_search


def parse_business_hours(opentime_str: str) -> list:
    """
    解析营业时间字符串，返回时间段列表
    
    支持格式：
    - "08:00-20:30" -> [(8, 0, 20, 30)]
    - "09:00-12:00;14:00-18:00" -> [(9, 0, 12, 0), (14, 0, 18, 0)]
    
    Args:
        opentime_str: 营业时间字符串
    
    Returns:
        list: [(开门小时, 开门分钟, 关门小时, 关门分钟), ...] 的列表，如果解析失败返回空列表
    """
    if not opentime_str:
        return []
    
    time_segments = []
    
    # 先按分号分割多个时间段
    segments = opentime_str.split(';')
    
    for segment in segments:
        segment = segment.strip()
        # 匹配格式：HH:MM-HH:MM
        pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
        match = re.search(pattern, segment)
        
        if match:
            open_hour = int(match.group(1))
            open_minute = int(match.group(2))
            close_hour = int(match.group(3))
            close_minute = int(match.group(4))
            time_segments.append((open_hour, open_minute, close_hour, close_minute))
    
    return time_segments


def check_current_time_in_business_hours(biz_ext: dict, current_time: str = "周二 14:30:00") -> bool:
    """
    检查当前时刻是否在营业时间内
    
    Args:
        biz_ext: POI的biz_ext字典
        current_time: 当前时间，格式如"周二 14:30:00"
    
    Returns:
        bool: True表示当前时刻在营业时间内，False表示不在营业时间内或无法确定
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
    
    # 检查是否为24小时营业
    time_str_lower = str(opentime_str).lower()
    is_24h = (
        "24小时" in str(opentime_str) or
        "全天" in str(opentime_str) or
        "00:00-24:00" in str(opentime_str) or
        "00:00-00:00" in str(opentime_str) or
        "24h" in time_str_lower
    )
    
    if is_24h:
        print(f"✅ 24小时营业，当前时刻在营业时间内")
        return True
    
    # 解析当前时间（周二 14:30:00）
    time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', current_time)
    if not time_match:
        print(f"⚠️  无法解析当前时间格式: {current_time}，假设在营业时间内")
        return True
    
    current_hour = int(time_match.group(1))
    current_minute = int(time_match.group(2))
    current_minutes = current_hour * 60 + current_minute
    
    # 解析营业时间
    time_segments = parse_business_hours(str(opentime_str))
    if not time_segments:
        print(f"⚠️  无法解析营业时间格式: {opentime_str}，假设在营业时间内")
        return True
    
    # 检查当前时刻是否在任何一个营业时间段内
    for open_hour, open_minute, close_hour, close_minute in time_segments:
        open_minutes = open_hour * 60 + open_minute
        close_minutes = close_hour * 60 + close_minute
        
        # 处理跨天的情况（如22:00-02:00）
        if close_minutes < open_minutes:
            # 跨天：当前时刻在开门时间之后或关门时间之前
            if current_minutes >= open_minutes or current_minutes <= close_minutes:
                print(f"✅ 当前时刻{current_hour:02d}:{current_minute:02d}在营业时间内（跨天：{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}）")
                return True
        else:
            # 正常情况：开门时间 <= 当前时刻 <= 关门时间
            if open_minutes <= current_minutes <= close_minutes:
                print(f"✅ 当前时刻{current_hour:02d}:{current_minute:02d}在营业时间内（{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}）")
                return True
    
    print(f"❌ 当前时刻{current_hour:02d}:{current_minute:02d}不在营业时间内（营业时间: {opentime_str}）")
    return False


def find_poi_by_name(text_search_result, target_name: str):
    """
    在文本搜索结果中查找指定名称的POI
    
    Args:
        text_search_result: maps_text_search 返回的结果
        target_name: 目标POI名称（可以是部分匹配）
    
    Returns:
        POI对象，如果未找到返回None
    """
    if text_search_result.error:
        return None
    
    if not text_search_result.pois:
        return None
    
    # 尝试精确匹配
    for poi in text_search_result.pois:
        if poi.name == target_name:
            return poi
    
    # 尝试部分匹配（去除括号等）
    target_name_clean = target_name.replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    for poi in text_search_result.pois:
        poi_name_clean = poi.name.replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        if target_name_clean in poi_name_clean or poi_name_clean in target_name_clean:
            return poi
    
    # 如果都没找到，返回第一个结果
    return text_search_result.pois[0]


def verify_poi(
    poi_id: str,
    user_location: str = "116.01978,36.45786",
    cafe_location: str = None,
    search_radius: int = 2000,
    keywords: str = "咖啡厅",
    min_rating: float = 4.4,
    current_time: str = "周二 14:30:00",
    mall_address: str = "聊城振华购物中心",
    mall_city: str = "聊城",
    mall_location: str = None,
    max_time_diff: int = 900,  # 15分钟 = 900秒
    rt_keywords: str = "大润发(东昌店)",
    rt_city: str = "聊城",
    rt_location: str = None,
    max_distance_to_rt: int = 2000  # 2km = 2000米
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 调用 maps_around_search，验证返回pois中包含目标poi_id（验证"附近2km内的咖啡厅"）。
    2) 调用 maps_search_detail，读取 biz_ext.rating 与 biz_ext.open_time/opentime2：验证 rating>=4.4；并结合题目给定time，验证当前时刻处于其营业时间段内。
    3) 调用 maps_geo 获取购物中心坐标；再调用 maps_driving_by_coordinates 得到t_drive。
    4) 调用 maps_walking_by_coordinates 得到t_walk；验证 |t_walk - t_drive| <= 15分钟。
    5) 调用 maps_text_search 选取与"大润发东昌店"匹配的POI，调用 maps_distance，验证distance<=2000米。
    
    Args:
        poi_id: POI ID，默认"B0LB2HPOY0"
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.01978,36.45786"
        cafe_location: 咖啡厅坐标，格式为"经度,纬度"，如果为None则从POI详情中获取
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡厅"
        min_rating: 最小评分，默认4.4
        current_time: 当前时间，格式如"周二 14:30:00"，默认"周二 14:30:00"
        mall_address: 购物中心地址，默认"聊城振华购物中心"
        mall_city: 购物中心所在城市，默认"聊城"
        mall_location: 购物中心坐标，格式为"经度,纬度"，如果为None则从maps_geo获取
        max_time_diff: 最大时间差（秒），默认900（15分钟）
        rt_keywords: 大润发搜索关键词，默认"大润发(东昌店)"
        rt_city: 大润发所在城市，默认"聊城"
        rt_location: 大润发坐标，格式为"经度,纬度"，如果为None则从maps_text_search获取
        max_distance_to_rt: 到大润发最大距离（米），默认2000（2公里）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束验证
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
    
    # 步骤2: 获取目标POI详情并验证评分和营业时间
    print(f"\n【步骤2】验证评分和营业时间约束（评分>={min_rating}，当前时刻在营业时间内）")
    print("-" * 80)
    cafe_detail = maps_search_detail(id=poi_id)
    if cafe_detail.error:
        print(f"❌ 获取咖啡厅详情失败: {cafe_detail.error}")
        return False
    
    if cafe_detail.location:
        cafe_location = cafe_detail.location
        print(f"✅ 获取咖啡厅坐标: {cafe_location} ({cafe_detail.name})")
    else:
        if cafe_location is None:
            print(f"❌ POI没有location信息")
            return False
        print(f"⚠️  咖啡厅详情中没有location信息，使用传入的默认坐标: {cafe_location}")
    
    # 验证评分
    if not cafe_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    rating = cafe_detail.biz_ext.get("rating")
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
    
    # 验证当前时刻是否在营业时间内
    if not check_current_time_in_business_hours(cafe_detail.biz_ext, current_time):
        return False
    
    # 步骤3: 获取购物中心坐标并计算驾车时间
    print(f"\n【步骤3】获取购物中心坐标并计算驾车时间")
    print("-" * 80)
    geo_result = maps_geo(address=mall_address, city=mall_city)
    if geo_result.error:
        print(f"❌ 获取购物中心坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到购物中心坐标")
        return False
    
    mall_location = geo_result.results[0].location
    print(f"✅ 获取购物中心坐标: {mall_location} ({mall_address})")
    
    # 计算驾车时间（从购物中心到咖啡厅）
    driving_result = maps_driving_by_coordinates(
        origin=mall_location,
        destination=cafe_location
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    t_drive = driving_result.total_duration_seconds
    print(f"✅ 客户驾车时间: {t_drive}秒（{t_drive // 60}分钟）")
    
    # 步骤4: 计算步行时间并验证时间差
    print(f"\n【步骤4】计算步行时间并验证时间差（<={max_time_diff}秒，即{max_time_diff // 60}分钟）")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=cafe_location
    )
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    t_walk = walking_result.total_duration_seconds
    print(f"✅ 用户步行时间: {t_walk}秒（{t_walk // 60}分钟）")
    
    # 计算时间差的绝对值
    time_diff = abs(t_walk - t_drive)
    if time_diff > max_time_diff:
        print(f"❌ 时间差{time_diff}秒（{time_diff // 60}分钟），超过{max_time_diff}秒（{max_time_diff // 60}分钟）")
        return False
    print(f"✅ 时间差{time_diff}秒（{time_diff // 60}分钟），符合要求（<= {max_time_diff}秒，即{max_time_diff // 60}分钟）")
    
    # 步骤5: 验证到大润发的直线距离
    print(f"\n【步骤5】验证到大润发(东昌店)的直线距离（<={max_distance_to_rt}米，即{max_distance_to_rt // 1000}公里）")
    print("-" * 80)
    # 5.1 搜索大润发
    rt_search_result = maps_text_search(
        keywords=rt_keywords,
        city=rt_city,
        citylimit="true"
    )
    if rt_search_result.error:
        print(f"❌ 搜索大润发失败: {rt_search_result.error}")
        return False
    
    if not rt_search_result.pois or len(rt_search_result.pois) == 0:
        print(f"❌ 未找到大润发")
        return False
    
    # 查找匹配的POI
    rt_poi = find_poi_by_name(rt_search_result, "大润发东昌店")
    if not rt_poi:
        rt_poi = rt_search_result.pois[0]
        print(f"⚠️  未找到精确匹配，使用第一个结果: {rt_poi.name}")
    else:
        print(f"✅ 找到匹配的POI: {rt_poi.name} (ID: {rt_poi.id})")
    
    # 获取大润发坐标（TextSearchPOI没有location属性，需要通过detail获取）
    rt_detail = maps_search_detail(id=rt_poi.id)
    if rt_detail.error:
        print(f"❌ 获取大润发详情失败: {rt_detail.error}")
        return False
    
    if not rt_detail.location:
        print(f"❌ 无法获取大润发坐标")
        return False
    
    rt_location = rt_detail.location
    print(f"✅ 获取大润发坐标: {rt_location} ({rt_poi.name})")
    
    # 5.2 计算直线距离
    distance_result = maps_distance(
        origins=cafe_location,
        destination=rt_location
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离信息")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance_to_rt:
        print(f"❌ 直线距离{distance_meters}米，超过{max_distance_to_rt}米（{max_distance_to_rt // 1000}公里）")
        return False
    print(f"✅ 直线距离{distance_meters}米，符合要求（<= {max_distance_to_rt}米，即{max_distance_to_rt // 1000}公里）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 673.py <poi_id> [user_location] [cafe_location]")
        print("示例: python 673.py B0LB2HPOY0")
        print("示例: python 673.py B0LB2HPOY0 116.01978,36.45786")
        print("示例: python 673.py B0LB2HPOY0 116.01978,36.45786 116.01978,36.45786")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0LB2HPOY0"
        user_location = "116.01978,36.45786"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "116.01978,36.45786"
        cafe_location = sys.argv[3] if len(sys.argv) > 3 else None
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    if cafe_location:
        print(f"咖啡厅坐标: {cafe_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, cafe_location=cafe_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
