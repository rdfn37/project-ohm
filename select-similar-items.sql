SELECT product_b AS similar_product, co_occurrences
FROM `project-ohm-******.ecom_core.co_visitation`
WHERE product_a = 'p8'
ORDER BY co_occurrences DESC
LIMIT 10;
