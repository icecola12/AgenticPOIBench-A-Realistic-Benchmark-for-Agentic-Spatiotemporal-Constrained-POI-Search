"""
修改任务指令：你想找你附近3公里内的商场。你准备骑车过去，所以骑行时间要在8分钟以内。办完事你还要直接开车去海口美兰国际机场，要求从这个商场开车到机场不超过30分钟。另外你要顺路寄个材料，所以这个商场周围200米内必须有邮局，并且商场评分要在4.5分及以上。你对服务和解决方案持怀疑态度。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location="110.347066,20.070703", radius="3000", keywords="商场")，且结果中包含 target_poi_id=B0FFHBAVLI。
2) 评分验证：对 target_poi_id 调用 maps_search_detail(id="B0FFHBAVLI")，读取 biz_ext.rating，验证 rating>=4.5。
3) 骑行时间验证：从上一步详情中取商场坐标 destination=location="110.349422,20.057666"，调用 maps_bicycling_by_coordinates(origin="110.347066,20.070703", destination="110.349422,20.057666")，验证 total_duration_seconds<=480（8分钟）。
4) 机场驾车时间验证：调用 maps_search_detail(id="B03820000A") 获取海口美兰国际机场坐标 location="110.467385,19.942495"；再调用 maps_driving_by_coordinates(origin="110.349422,20.057666", destination="110.467385,19.942495")，验证 total_duration_seconds<=1800（30分钟）。
5) 邮局邻近验证：以商场坐标为中心调用 maps_around_search(location="110.349422,20.057666", radius="200", keywords="邮局")，验证 pois 非空（>=1）。
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
    maps_driving_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.347066,20.070703",
    mall_location: str = "110.349422,20.057666",
    airport_poi_id: str = "B03820000A",
    airport_location: str = "110.467385,19.942495",
    search_radius: int = 3000,
    keywords: str = "商场",
    min_rating: float = 4.5,
    max_bicycling_duration: int = 480,  # 8分钟 = 480秒
    max_driving_duration: int = 1800,  # 30分钟 = 1800秒
    post_office_search_radius: int = 200,
    post_office_keywords: str = "邮局"
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边范围验证：调用 maps_around_search，且结果中包含目标poi_id。
    2) 评分验证：调用 maps_search_detail，读取 biz_ext.rating，验证 rating>=4.5。
    3) 骑行时间验证：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds<=480（8分钟）。
    4) 机场驾车时间验证：调用 maps_search_detail 获取机场坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds<=1800（30分钟）。
    5) 邮局邻近验证：以商场坐标为中心调用 maps_around_search，验证 pois 非空（>=1）。
    
    Args:
        poi_id: POI ID，默认"B0FFHBAVLI"
        user_location: 用户坐标，格式为"经度,纬度"，默认"110.347066,20.070703"
        mall_location: 商场坐标，格式为"经度,纬度"，默认"110.349422,20.057666"
        airport_poi_id: 机场POI ID，默认"B03820000A"
        airport_location: 机场坐标，格式为"经度,纬度"，默认"110.467385,19.942495"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"商场"
        min_rating: 最小评分，默认4.5
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        max_driving_duration: 最大驾车时长（秒），默认1800（30分钟）
        post_office_search_radius: 邮局搜索半径（米），默认200
        post_office_keywords: 邮局搜索关键词，默认"邮局"
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证
    print(f"【步骤1】验证周边范围（{search_radius}米范围内，关键词：{keywords}）")
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
    
    # 步骤2: 评分验证
    print(f"\n【步骤2】验证评分（>={min_rating}分）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
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
    
    # 获取商场坐标（如果详情中有location，使用详情中的；否则使用传入的默认值）
    if poi_detail.location:
        mall_location = poi_detail.location
        print(f"✅ 获取商场坐标: {mall_location} ({poi_detail.name})")
    else:
        print(f"⚠️  POI详情中没有location信息，使用默认坐标: {mall_location}")
    
    # 步骤3: 骑行时间验证
    print(f"\n【步骤3】验证骑行时间（<={max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=mall_location
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
    
    # 步骤4: 机场驾车时间验证
    print(f"\n【步骤4】验证机场驾车时间（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    # 获取机场坐标
    airport_detail = maps_search_detail(id=airport_poi_id)
    if airport_detail.error:
        print(f"❌ 获取机场详情失败: {airport_detail.error}")
        return False
    
    if airport_detail.location:
        airport_location = airport_detail.location
        print(f"✅ 获取机场坐标: {airport_location} ({airport_detail.name})")
    else:
        print(f"⚠️  机场详情中没有location信息，使用默认坐标: {airport_location}")
    
    # 计算驾车时间
    driving_result = maps_driving_by_coordinates(
        origin=mall_location,
        destination=airport_location
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
    
    # 步骤5: 邮局邻近验证
    print(f"\n【步骤5】验证邮局邻近（{post_office_search_radius}米范围内）")
    print("-" * 80)
    post_office_search_result = maps_around_search(
        location=mall_location,
        radius=str(post_office_search_radius),
        keywords=post_office_keywords
    )
    if post_office_search_result.error:
        print(f"❌ 搜索邮局失败: {post_office_search_result.error}")
        return False
    
    if not post_office_search_result.pois or len(post_office_search_result.pois) == 0:
        print(f"❌ 未找到邮局")
        return False
    
    print(f"✅ 找到邮局: {post_office_search_result.pois[0].name} (共{len(post_office_search_result.pois)}个)")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 583.py <poi_id> [user_location] [mall_location]")
        print("示例: python 583.py B0FFHBAVLI")
        print("示例: python 583.py B0FFHBAVLI 110.347066,20.070703")
        print("示例: python 583.py B0FFHBAVLI 110.347066,20.070703 110.349422,20.057666")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0FFHBAVLI"
        user_location = "110.347066,20.070703"
        mall_location = "110.349422,20.057666"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "110.347066,20.070703"
        mall_location = sys.argv[3] if len(sys.argv) > 3 else "110.349422,20.057666"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print(f"商场坐标: {mall_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, mall_location=mall_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
