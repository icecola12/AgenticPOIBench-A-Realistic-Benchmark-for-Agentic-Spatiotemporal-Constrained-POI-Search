"""
修改任务指令：你想在附近2公里内找一家诊所，打算先骑车过去，骑行时间得在15分钟内；如果临时改成走路，也要能在25分钟内走到。诊所附近1.2公里内必须有地铁站。另外你之后要去郑州火车站赶车，所以从诊所开车到郑州火车站必须在10分钟内。你虽然心情不好，但仍然保持礼貌和独立的姿态。
# 注意：首个约束已修正为"你想在附近2公里内找一家诊所"（强调"附近指定距离内"，而非"不超过指定距离"）

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束：调用 maps_around_search，以用户坐标(113.644769,34.764205)为中心、radius=2000、keywords=诊所，验证返回pois中包含目标poi_id=B0JR91JVTO。  
2) 获取诊所坐标：调用 maps_search_detail(B0JR91JVTO)，读取location=113.644402,34.764907。  
3) 骑行时间约束：调用 maps_bicycling_by_coordinates(origin=113.644769,34.764205, destination=113.644402,34.764907)，验证 total_duration_seconds <= 900。  
4) 步行时间约束：调用 maps_walking_by_coordinates(origin=113.644769,34.764205, destination=113.644402,34.764907)，验证 total_duration_seconds <= 1500。  
5) 地铁站邻近约束：调用 maps_around_search(location=113.644402,34.764907, radius=1200, keywords=地铁站) 获取附近地铁站列表,验证列表长度 >= 1。
6) 去火车站驾车时间约束：调用 maps_text_search(keywords=郑州火车站, city=郑州, citylimit=true) 选取POI"郑州站"(id=B01730K2X2)；调用 maps_search_detail(B01730K2X2)获取location=113.658097,34.745795；调用 maps_driving_by_coordinates(origin=113.644402,34.764907, destination=113.658097,34.745795)，验证 total_duration_seconds <= 600。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_driving_by_coordinates,
    maps_text_search
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.644769,34.764205",
    clinic_location: str = "113.644402,34.764907",
    search_radius: int = 2000,
    keywords: str = "诊所",
    max_bicycling_duration: int = 900,  # 15分钟 = 900秒
    max_walking_duration: int = 1500,  # 25分钟 = 1500秒
    subway_search_radius: int = 1200,
    subway_keywords: str = "地铁站",
    train_station_keywords: str = "郑州火车站",
    train_station_city: str = "郑州",
    train_station_poi_id: str = "B01730K2X2",
    train_station_location: str = "113.658097,34.745795",
    max_driving_duration: int = 600  # 10分钟 = 600秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边约束：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 获取诊所坐标：调用 maps_search_detail，读取location。
    3) 骑行时间约束：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 900。
    4) 步行时间约束：调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1500。
    5) 地铁站邻近约束：调用 maps_around_search，验证列表长度 >= 1。
    6) 去火车站驾车时间约束：调用 maps_text_search 和 maps_search_detail 获取火车站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 600。
    
    Args:
        poi_id: POI ID，默认"B0JR91JVTO"
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.644769,34.764205"
        clinic_location: 诊所坐标，格式为"经度,纬度"，默认"113.644402,34.764907"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"诊所"
        max_bicycling_duration: 最大骑行时长（秒），默认900（15分钟）
        max_walking_duration: 最大步行时长（秒），默认1500（25分钟）
        subway_search_radius: 地铁站搜索半径（米），默认1200（1.2公里）
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        train_station_keywords: 火车站搜索关键词，默认"郑州火车站"
        train_station_city: 火车站所在城市，默认"郑州"
        train_station_poi_id: 火车站POI ID，默认"B01730K2X2"
        train_station_location: 火车站坐标，格式为"经度,纬度"，默认"113.658097,34.745795"
        max_driving_duration: 最大驾车时长（秒），默认600（10分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束
    print(f"【步骤1】验证周边约束（{search_radius}米范围内，关键词：{keywords}）")
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
    
    # 步骤2: 获取诊所坐标
    print(f"\n【步骤2】获取诊所坐标")
    print("-" * 80)
    clinic_detail = maps_search_detail(id=poi_id)
    if clinic_detail.error:
        print(f"❌ 获取诊所详情失败: {clinic_detail.error}")
        return False
    
    if clinic_detail.location:
        clinic_location = clinic_detail.location
        print(f"✅ 获取诊所坐标: {clinic_location} ({clinic_detail.name})")
    else:
        print(f"⚠️  诊所详情中没有location信息，使用默认坐标: {clinic_location}")
    
    # 步骤3: 骑行时间约束
    print(f"\n【步骤3】验证骑行时间约束（<={max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=clinic_location
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False
    
    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    
    # 步骤4: 步行时间约束
    print(f"\n【步骤4】验证步行时间约束（<={max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=clinic_location
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
    
    # 步骤5: 地铁站邻近约束
    print(f"\n【步骤5】验证地铁站邻近约束（{subway_search_radius}米范围内）")
    print("-" * 80)
    subway_search_result = maps_around_search(
        location=clinic_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False
    
    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False
    
    print(f"✅ 找到地铁站: {subway_search_result.pois[0].name} (共{len(subway_search_result.pois)}个)")
    
    # 步骤6: 去火车站驾车时间约束
    print(f"\n【步骤6】验证去火车站驾车时间约束（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    # 6.1 搜索郑州火车站
    train_station_search_result = maps_text_search(
        keywords=train_station_keywords,
        city=train_station_city,
        citylimit="true"
    )
    if train_station_search_result.error:
        print(f"❌ 搜索火车站失败: {train_station_search_result.error}")
        return False
    
    if not train_station_search_result.pois:
        print(f"❌ 未找到火车站")
        return False
    
    # 查找目标火车站POI（郑州站）
    train_station_found = False
    train_station_location_actual = train_station_location
    for poi in train_station_search_result.pois:
        if poi.id == train_station_poi_id:
            train_station_found = True
            print(f"✅ 找到目标火车站: {poi.name} (ID: {train_station_poi_id})")
            break
    
    if not train_station_found:
        print(f"⚠️  未在搜索结果中找到目标火车站ID {train_station_poi_id}，使用默认坐标")
    
    # 6.2 获取火车站坐标
    train_station_detail = maps_search_detail(id=train_station_poi_id)
    if train_station_detail.error:
        print(f"❌ 获取火车站详情失败: {train_station_detail.error}")
        return False
    
    if train_station_detail.location:
        train_station_location_actual = train_station_detail.location
        print(f"✅ 获取火车站坐标: {train_station_location_actual} ({train_station_detail.name})")
    else:
        print(f"⚠️  火车站详情中没有location信息，使用默认坐标: {train_station_location_actual}")
    
    # 6.3 计算驾车时间
    driving_result = maps_driving_by_coordinates(
        origin=clinic_location,
        destination=train_station_location_actual
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
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 603.py <poi_id> [user_location] [clinic_location]")
        print("示例: python 603.py B0JR91JVTO")
        print("示例: python 603.py B0JR91JVTO 113.644769,34.764205")
        print("示例: python 603.py B0JR91JVTO 113.644769,34.764205 113.644402,34.764907")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0JR91JVTO"
        user_location = "113.644769,34.764205"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "113.644769,34.764205"
        clinic_location = sys.argv[3] if len(sys.argv) > 3 else "113.644402,34.764907"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print(f"诊所坐标: {clinic_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, clinic_location=clinic_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
