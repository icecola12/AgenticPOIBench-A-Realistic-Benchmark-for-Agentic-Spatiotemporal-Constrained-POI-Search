
"""
修改任务指令：你想在附近2500米以内找一家网吧。为了方便接下来换乘长途车，你还要求从你这里出发先到网吧、再去玉林汽车总站的总驾车时间不超过7分钟，而且相比直接从你这里开车去玉林汽车总站，绕路增加的时间也不能超过7分钟。另外，这家网吧不能在玉林火车站直线距离500米范围内。再加一个细节：你从你这里开车去网吧的路线里，第一个途径点附近300米内必须能找到一家银行。你说话非常有条理和注重细节
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1） 玉林汽车总站坐标B(由maps_text_search+maps_search_detail获得)；玉林火车站坐标S(由maps_text_search+maps_search_detail获得)；目标网吧P(由maps_search_detail获得)。
2) 附近2500米内网吧：调用 maps_around_search(location=U, radius=2500, keywords='网吧')，验证返回pois中包含 target_poi_id。
3) 不在玉林火车站500米内：调用 maps_search_detail(target_poi_id) 得到P坐标；调用 maps_distance(origins=S, destination=P)，验证直线距离>500米。
4) 从U经由P到B总驾车时间≤7分钟：调用 maps_driving_by_coordinates(origin=U, destination=P) 得到t_UP；调用 maps_driving_by_coordinates(origin=P, destination=B) 得到t_PB；验证 (t_UP+t_PB)/60 ≤ 7。
5) 绕行增加时间≤7分钟：调用 maps_driving_by_coordinates(origin=U, destination=B) 得到t_UB；验证 ((t_UP+t_PB)-t_UB)/60 ≤ 7。
6) 第一个途径点300米内有银行：取步骤1中的第一条 DrivingStep 的 to_coordinates 作为第一个途径点C；调用 maps_around_search(location=C, radius=300, keywords='银行')，验证 pois 非空。
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
    maps_text_search,
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.156631,22.61243",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "网吧",
    bus_station_address: str = "玉林汽车总站",
    bus_station_city: str = "玉林",
    train_station_address: str = "玉林火车站",
    train_station_city: str = "玉林",
    min_distance_from_train_station: int = 500,  # 500 meters
    max_total_driving_duration: int = 420,  # 7 minutes = 420 seconds
    max_detour_duration: int = 420,  # 7 minutes = 420 seconds
    bank_search_radius: int = 300,  # 300 meters
    bank_keywords: str = "银行"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2500米内网吧：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 不在玉林火车站500米内：调用 maps_search_detail 得到P坐标，调用 maps_distance，验证直线距离>500米。
    3) 从U经由P到B总驾车时间≤7分钟：调用 maps_driving_by_coordinates 得到t_UP和t_PB，验证 (t_UP+t_PB)/60 ≤ 7。
    4) 绕行增加时间≤7分钟：调用 maps_driving_by_coordinates 得到t_UB，验证 ((t_UP+t_PB)-t_UB)/60 ≤ 7。
    5) 第一个途径点300米内有银行：取第一条 DrivingStep 的 to_coordinates 作为第一个途径点C，调用 maps_around_search，验证 pois 非空。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"110.156631,22.61243"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"网吧"
        bus_station_address: 汽车总站地址，默认"玉林汽车总站"
        bus_station_city: 汽车总站所在城市，默认"玉林"
        train_station_address: 火车站地址，默认"玉林火车站"
        train_station_city: 火车站所在城市，默认"玉林"
        min_distance_from_train_station: 距离火车站最小距离（米），默认500
        max_total_driving_duration: 最大总驾车时长（秒），默认420（7分钟）
        max_detour_duration: 最大绕行时长（秒），默认420（7分钟）
        bank_search_radius: 银行搜索半径（米），默认300
        bank_keywords: 银行搜索关键词，默认"银行"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2500米内网吧
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

    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 获取玉林汽车总站坐标
    bus_station_text_search_result = maps_text_search(keywords=bus_station_address, city=bus_station_city)
    if bus_station_text_search_result.error:
        print(f"❌ 获取汽车总站坐标失败: {bus_station_text_search_result.error}")
        return False

    if not bus_station_text_search_result.pois or len(bus_station_text_search_result.pois) == 0:
        print(f"❌ 未找到汽车总站坐标")
        return False

    bus_station_poi_id = bus_station_text_search_result.pois[0].id
    bus_station_detail_result = maps_search_detail(id=bus_station_poi_id)
    if bus_station_detail_result.error:
        print(f"❌ 获取汽车总站详情失败: {bus_station_detail_result.error}")
        return False
    if not bus_station_detail_result.location:
        print(f"❌ 汽车总站没有location信息")
        return False
    bus_station_location = bus_station_detail_result.location
    print(f"✅ 获取汽车总站坐标: {bus_station_location} ({bus_station_address})")

    # 步骤4: 获取玉林火车站坐标
    train_station_text_search_result = maps_text_search(keywords=train_station_address, city=train_station_city)
    if train_station_text_search_result.error:
        print(f"❌ 获取火车站坐标失败: {train_station_text_search_result.error}")
        return False

    if not train_station_text_search_result.pois or len(train_station_text_search_result.pois) == 0:
        print(f"❌ 未找到火车站坐标")
        return False

    train_station_poi_id = train_station_text_search_result.pois[0].id
    train_station_detail_result = maps_search_detail(id=train_station_poi_id)
    if train_station_detail_result.error:
        print(f"❌ 获取火车站详情失败: {train_station_detail_result.error}")
        return False
    if not train_station_detail_result.location:
        print(f"❌ 火车站没有location信息")
        return False
    train_station_location = train_station_detail_result.location
    print(f"✅ 获取火车站坐标: {train_station_location} ({train_station_address})")

    # 步骤5: 验证不在玉林火车站500米内
    distance_result = maps_distance(origins=train_station_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离信息")
        return False

    distance_from_train_station = distance_result.results[0].distance_meters
    if distance_from_train_station <= min_distance_from_train_station:
        print(f"❌ POI距离火车站{distance_from_train_station}米，不符合要求（需要>{min_distance_from_train_station}米）")
        return False
    print(f"✅ POI距离火车站{distance_from_train_station}米，符合要求（> {min_distance_from_train_station}米）")

    # 步骤6: 计算从用户位置到POI的驾车时间（t_UP）
    driving_u_to_p_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_u_to_p_result.error:
        print(f"❌ 计算从用户位置到POI的驾车路线失败: {driving_u_to_p_result.error}")
        return False

    if driving_u_to_p_result.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到POI的驾车时长")
        return False

    t_UP = driving_u_to_p_result.total_duration_seconds
    print(f"✅ 从用户位置到POI的驾车时长: {t_UP}秒（{t_UP // 60}分{t_UP % 60}秒）")

    # 步骤7: 计算从POI到汽车总站的驾车时间（t_PB）
    driving_p_to_b_result = maps_driving_by_coordinates(origin=poi_location, destination=bus_station_location)
    if driving_p_to_b_result.error:
        print(f"❌ 计算从POI到汽车总站的驾车路线失败: {driving_p_to_b_result.error}")
        return False

    if driving_p_to_b_result.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到汽车总站的驾车时长")
        return False

    t_PB = driving_p_to_b_result.total_duration_seconds
    print(f"✅ 从POI到汽车总站的驾车时长: {t_PB}秒（{t_PB // 60}分{t_PB % 60}秒）")

    # 步骤8: 验证总驾车时间≤7分钟
    total_driving_duration = t_UP + t_PB
    if total_driving_duration > max_total_driving_duration:
        print(f"❌ 总驾车时长{total_driving_duration}秒（{total_driving_duration // 60}分{total_driving_duration % 60}秒），超过{max_total_driving_duration}秒（{max_total_driving_duration // 60}分钟）")
        return False
    print(f"✅ 总驾车时长{total_driving_duration}秒（{total_driving_duration // 60}分{total_driving_duration % 60}秒），符合要求（<= {max_total_driving_duration}秒，即{max_total_driving_duration // 60}分钟）")

    # 步骤9: 计算从用户位置直接到汽车总站的驾车时间（t_UB）
    driving_u_to_b_result = maps_driving_by_coordinates(origin=user_location, destination=bus_station_location)
    if driving_u_to_b_result.error:
        print(f"❌ 计算从用户位置到汽车总站的驾车路线失败: {driving_u_to_b_result.error}")
        return False

    if driving_u_to_b_result.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到汽车总站的驾车时长")
        return False

    t_UB = driving_u_to_b_result.total_duration_seconds
    print(f"✅ 从用户位置直接到汽车总站的驾车时长: {t_UB}秒（{t_UB // 60}分{t_UB % 60}秒）")

    # 步骤10: 验证绕行增加时间≤7分钟
    detour_duration = total_driving_duration - t_UB
    if detour_duration > max_detour_duration:
        print(f"❌ 绕行增加时长{detour_duration}秒（{detour_duration // 60}分{detour_duration % 60}秒），超过{max_detour_duration}秒（{max_detour_duration // 60}分钟）")
        return False
    print(f"✅ 绕行增加时长{detour_duration}秒（{detour_duration // 60}分{detour_duration % 60}秒），符合要求（<= {max_detour_duration}秒，即{max_detour_duration // 60}分钟）")

    # 步骤11: 验证第一个途径点300米内有银行
    if not driving_u_to_p_result.steps or len(driving_u_to_p_result.steps) == 0:
        print(f"❌ 无法获取驾车路线的分步信息")
        return False

    first_waypoint = driving_u_to_p_result.steps[0].to_coordinates
    print(f"✅ 获取第一个途径点坐标: {first_waypoint}")

    bank_search_result = maps_around_search(
        location=first_waypoint,
        radius=str(bank_search_radius),
        keywords=bank_keywords
    )
    if bank_search_result.error:
        print(f"❌ 搜索银行失败: {bank_search_result.error}")
        return False

    if not bank_search_result.pois or len(bank_search_result.pois) == 0:
        print(f"❌ 第一个途径点{bank_search_radius}米范围内未找到银行")
        return False

    print(f"✅ 第一个途径点{bank_search_radius}米范围内找到银行: {bank_search_result.pois[0].name} (共{len(bank_search_result.pois)}个)")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 851.py 文件...\\n")
    result = verify_poi(poi_id="B0FFMFU9WK")
    print(f"\n验证结果: {result}")
