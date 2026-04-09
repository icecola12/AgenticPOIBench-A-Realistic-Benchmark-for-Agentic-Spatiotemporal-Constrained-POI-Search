"""
修改任务指令：你想找一个附近2公里内的咖啡厅，方便接下来和客户在店里把合同细节敲定。你希望这家店在今天10:00到20:00之间是营业状态。为了沟通效率，咖啡厅在高德上的评分得在4.3分及以上。你还需要它到其周边1.5km范围内任意公交站的最短步行通行时间不超过15分钟，方便客户坐公交过来。最后，为了不耽误你接下来的行程，你从当前位置步行到咖啡厅的时间要控制在20分钟以内。你一个喜欢开玩笑的有趣的人，试图让对话变得轻松。
# 注意：首个约束已修正为"你想找一个附近2公里内的咖啡厅"（原表述为"你要找一个附近2公里内的咖啡厅"）

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（2公里内 & POI类型为咖啡厅）：调用 maps_around_search(location="116.020702,36.456375", radius="2000", keywords="咖啡厅")，验证返回pois中包含目标poi_id=B0L6JYS34L。  
2) 营业时间约束（今天10:00-20:00之间处于营业）：调用 maps_search_detail(id="B0L6JYS34L")，读取 biz_ext.open_time 或 biz_ext.opentime2，验证其营业时间覆盖 10:00-20:00（例如 08:00-20:30 覆盖该区间）。  
3) 评分约束（>=4.3）：同样通过 maps_search_detail(id="B0L6JYS34L") 获取 biz_ext.rating，验证 rating>=4.3。  
4) 步行到公交站<=15分钟：  
4.1 调用 maps_search_detail(id="B0L6JYS34L") 获取咖啡厅坐标location。  
4.2 以该location为中心调用 maps_around_search(location=咖啡厅location, radius="1500", keywords="公交站") 获取附近公交站POI列表（至少应包含 BV09296589）。  
4.3 对候选公交站逐个调用 maps_walking_by_coordinates(origin=咖啡厅location, destination=公交站location)，取最小步行时长t_bus，验证 t_bus<=900秒。  
5) 你到咖啡厅步行<=20分钟：调用 maps_walking_by_coordinates(origin="116.020702,36.456375", destination=咖啡厅location)，得到步行时长t_walk，验证 t_walk<=1200秒。
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


def check_business_hours_cover_time_range(biz_ext: dict, required_start_hour: int = 10, required_start_minute: int = 0, 
                                          required_end_hour: int = 20, required_end_minute: int = 0) -> bool:
    """
    检查营业时间是否覆盖指定的时间段（10:00-20:00）
    
    Args:
        biz_ext: POI的biz_ext字典
        required_start_hour: 要求的开始时间（小时），默认10
        required_start_minute: 要求的开始时间（分钟），默认0
        required_end_hour: 要求的结束时间（小时），默认20
        required_end_minute: 要求的结束时间（分钟），默认0
    
    Returns:
        bool: True表示营业时间覆盖指定时间段，False表示不符合要求或无法确定
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
    
    # 解析营业时间
    time_segments = parse_business_hours(opentime_str)
    if not time_segments:
        print(f"❌ 无法解析营业时间格式: {opentime_str}")
        return False
    
    # 计算要求的时间段（分钟）
    required_start_minutes = required_start_hour * 60 + required_start_minute
    required_end_minutes = required_end_hour * 60 + required_end_minute
    
    # 检查是否有任何一个时间段覆盖了要求的时间段
    for open_hour, open_minute, close_hour, close_minute in time_segments:
        open_minutes = open_hour * 60 + open_minute
        close_minutes = close_hour * 60 + close_minute
        
        # 处理跨天的情况（如22:00-02:00）
        if close_minutes < open_minutes:
            # 跨天，需要特殊处理
            # 如果要求的时间段也在跨天范围内，需要检查
            if required_start_minutes >= open_minutes or required_end_minutes <= close_minutes:
                # 要求的时间段在跨天范围内
                if required_start_minutes >= open_minutes and required_end_minutes <= (24 * 60 + close_minutes):
                    print(f"✅ 营业时间{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}覆盖要求时间段{required_start_hour:02d}:{required_start_minute:02d}-{required_end_hour:02d}:{required_end_minute:02d}")
                    return True
        else:
            # 正常情况：开门时间 <= 要求开始时间 且 关门时间 >= 要求结束时间
            if open_minutes <= required_start_minutes and close_minutes >= required_end_minutes:
                print(f"✅ 营业时间{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}覆盖要求时间段{required_start_hour:02d}:{required_start_minute:02d}-{required_end_hour:02d}:{required_end_minute:02d}")
                return True
    
    print(f"❌ 营业时间不覆盖要求时间段{required_start_hour:02d}:{required_start_minute:02d}-{required_end_hour:02d}:{required_end_minute:02d}")
    return False


def verify_poi(
    poi_id: str,
    user_location: str = "116.020702,36.456375",
    search_radius: int = 2000,
    keywords: str = "咖啡厅",
    min_rating: float = 4.3,
    bus_stop_search_radius: int = 1500,
    bus_stop_keywords: str = "公交站",
    max_walking_to_bus_stop_duration: int = 900,  # 15分钟 = 900秒
    max_walking_to_poi_duration: int = 1200,  # 20分钟 = 1200秒
    required_start_hour: int = 10,
    required_start_minute: int = 0,
    required_end_hour: int = 20,
    required_end_minute: int = 0
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 距离约束（2公里内 & POI类型为咖啡厅）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 营业时间约束（今天10:00-20:00之间处于营业）：调用 maps_search_detail，读取 biz_ext.open_time 或 biz_ext.opentime2，验证其营业时间覆盖 10:00-20:00。
    3) 评分约束（>=4.3）：通过 maps_search_detail 获取 biz_ext.rating，验证 rating>=4.3。
    4) 步行到公交站<=15分钟：获取咖啡厅坐标，搜索附近公交站，计算最小步行时长，验证 <=900秒。
    5) 用户到咖啡厅步行<=20分钟：调用 maps_walking_by_coordinates，验证步行时长 <=1200秒。
    
    Args:
        poi_id: POI ID，默认"B0L6JYS34L"
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.020702,36.456375"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡厅"
        min_rating: 最小评分，默认4.3
        bus_stop_search_radius: 公交站搜索半径（米），默认1500（1.5公里）
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_walking_to_bus_stop_duration: 到公交站最大步行时长（秒），默认900（15分钟）
        max_walking_to_poi_duration: 到咖啡厅最大步行时长（秒），默认1200（20分钟）
        required_start_hour: 要求的营业开始时间（小时），默认10
        required_start_minute: 要求的营业开始时间（分钟），默认0
        required_end_hour: 要求的营业结束时间（小时），默认20
        required_end_minute: 要求的营业结束时间（分钟），默认0
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（2公里内 & POI类型为咖啡厅）
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
    
    # 步骤2: 营业时间约束（今天10:00-20:00之间处于营业）
    print(f"\n【步骤2】验证营业时间约束（营业时间覆盖{required_start_hour:02d}:{required_start_minute:02d}-{required_end_hour:02d}:{required_end_minute:02d}）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 验证营业时间覆盖10:00-20:00
    if not check_business_hours_cover_time_range(
        poi_detail.biz_ext,
        required_start_hour=required_start_hour,
        required_start_minute=required_start_minute,
        required_end_hour=required_end_hour,
        required_end_minute=required_end_minute
    ):
        return False
    
    # 步骤3: 评分约束（>=4.3）
    print(f"\n【步骤3】验证评分约束（>={min_rating}）")
    print("-" * 80)
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
    
    # 获取咖啡厅坐标
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    cafe_location = poi_detail.location
    print(f"✅ 获取咖啡厅坐标: {cafe_location} ({poi_detail.name})")
    
    # 步骤4: 步行到公交站<=15分钟
    print(f"\n【步骤4】验证步行到公交站时长（<={max_walking_to_bus_stop_duration}秒，即{max_walking_to_bus_stop_duration // 60}分钟）")
    print("-" * 80)
    # 4.1 搜索附近公交站
    bus_stop_search_result = maps_around_search(
        location=cafe_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False
    
    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False
    
    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")
    
    # 4.2 对每个公交站计算步行时间，取最小值
    min_walking_duration = None
    min_bus_stop_name = None
    
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue
        
        walking_result = maps_walking_by_coordinates(
            origin=cafe_location,
            destination=bus_stop.location
        )
        
        if walking_result.error:
            print(f"⚠️  计算到公交站 {bus_stop.name} 的步行路线失败: {walking_result.error}")
            continue
        
        if walking_result.total_duration_seconds is None:
            print(f"⚠️  无法获取到公交站 {bus_stop.name} 的步行时长")
            continue
        
        walking_duration = walking_result.total_duration_seconds
        if min_walking_duration is None or walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            min_bus_stop_name = bus_stop.name
    
    if min_walking_duration is None:
        print(f"❌ 无法计算到任何公交站的步行时长")
        return False
    
    if min_walking_duration > max_walking_to_bus_stop_duration:
        print(f"❌ 到最近公交站（{min_bus_stop_name}）的步行时长{min_walking_duration}秒，超过{max_walking_to_bus_stop_duration}秒（{max_walking_to_bus_stop_duration // 60}分钟）")
        return False
    print(f"✅ 到最近公交站（{min_bus_stop_name}）的步行时长{min_walking_duration}秒，符合要求（<= {max_walking_to_bus_stop_duration}秒，即{max_walking_to_bus_stop_duration // 60}分钟）")
    
    # 步骤5: 用户到咖啡厅步行<=20分钟
    print(f"\n【步骤5】验证用户到咖啡厅步行时长（<={max_walking_to_poi_duration}秒，即{max_walking_to_poi_duration // 60}分钟）")
    print("-" * 80)
    walking_result_user_to_cafe = maps_walking_by_coordinates(
        origin=user_location,
        destination=cafe_location
    )
    if walking_result_user_to_cafe.error:
        print(f"❌ 计算步行路线失败: {walking_result_user_to_cafe.error}")
        return False
    
    if walking_result_user_to_cafe.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    walking_duration_user_to_cafe = walking_result_user_to_cafe.total_duration_seconds
    if walking_duration_user_to_cafe > max_walking_to_poi_duration:
        print(f"❌ 步行时长{walking_duration_user_to_cafe}秒，超过{max_walking_to_poi_duration}秒（{max_walking_to_poi_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration_user_to_cafe}秒，符合要求（<= {max_walking_to_poi_duration}秒，即{max_walking_to_poi_duration // 60}分钟）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 601.py <poi_id> [user_location]")
        print("示例: python 601.py B0L6JYS34L")
        print("示例: python 601.py B0L6JYS34L 116.020702,36.456375")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0L6JYS34L"
        user_location = "116.020702,36.456375"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "116.020702,36.456375"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
