
"""
修改任务指令：你想找一个附近2500米的购物中心，开车过去别超过8分钟。另外你需要在这个购物中心周边300米内能搜到图文/复印店，周边500米内还得有公交站。你"自信、有条理、有创造力，但没有耐心。"
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（不超过2500米）：调用 maps_around_search({location: '119.656134,29.063638', radius:'2500', keywords:'购物中心'})，验证返回pois中包含 target_poi_id='B02430HT57'。
2) 驾车时间约束（≤8分钟）：调用 maps_search_detail({id:'B02430HT57'}) 获取其location='119.657953,29.065212'；再调用 maps_driving_by_coordinates({origin:'119.656134,29.063638', destination:'119.657953,29.065212'})，验证 total_duration_seconds ≤ 480。
3) 周边300米有图文/复印店：以目标POI坐标为中心调用 maps_around_search({location:'119.657953,29.065212', radius:'300', keywords:'图文'})和复印店，验证返回pois数量≥1。
4) 周边500米有公交站：以目标POI坐标为中心调用 maps_around_search({location:'119.657953,29.065212', radius:'500', keywords:'公交站'})，验证返回pois数量≥1。
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
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "119.656134,29.063638",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "购物中心",
    max_driving_duration: int = 480,  # 8 minutes = 480 seconds
    copy_shop_search_radius: int = 300,  # 300m
    copy_shop_keywords: str = "图文",
    bus_stop_search_radius: int = 500,  # 500m
    bus_stop_keywords: str = "公交站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束（不超过2500米）：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) 驾车时间约束（≤8分钟）：调用 maps_search_detail 获取其location；再调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 480。
    3) 周边300米有图文/复印店：以目标POI坐标为中心调用 maps_around_search，验证返回pois数量≥1。
    4) 周边500米有公交站：以目标POI坐标为中心调用 maps_around_search，验证返回pois数量≥1。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"119.656134,29.063638"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"购物中心"
        max_driving_duration: 最大驾车时长（秒），默认480（8分钟）
        copy_shop_search_radius: 图文/复印店搜索半径（米），默认300
        copy_shop_keywords: 图文/复印店搜索关键词，默认"图文"
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（不超过2500米）
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

    # 步骤2: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 驾车时间约束（≤8分钟）
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
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

    # 步骤4: 周边300米有图文/复印店
    copy_shop_search_result = maps_around_search(
        location=poi_location,
        radius=str(copy_shop_search_radius),
        keywords=copy_shop_keywords
    )
    if copy_shop_search_result.error:
        print(f"❌ 搜索图文/复印店失败: {copy_shop_search_result.error}")
        return False

    if not copy_shop_search_result.pois or len(copy_shop_search_result.pois) == 0:
        print(f"❌ 购物中心附近{copy_shop_search_radius}米内未找到图文/复印店")
        return False

    print(f"✅ 购物中心附近{copy_shop_search_radius}米内找到图文/复印店: {copy_shop_search_result.pois[0].name} (共{len(copy_shop_search_result.pois)}个)")

    # 步骤5: 周边500米有公交站
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 购物中心附近{bus_stop_search_radius}米内未找到公交站")
        return False

    print(f"✅ 购物中心附近{bus_stop_search_radius}米内找到公交站: {bus_stop_search_result.pois[0].name} (共{len(bus_stop_search_result.pois)}个)")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 728.py 文件...\n")
    result = verify_poi(poi_id="B02430HT57")
    print(f"\n验证结果: {result}")
