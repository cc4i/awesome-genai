# OCR
## 1. Extract information from various images in different languages: Thai, Vietnamese, Indonesian, etc  
- Translation
- Extracting
- Output with structure data: Json 
1 x Food item (Vietnamese) , 1 x driving license (Thai), 1 x bank invoice/statement (Bahasa)

### Prompt

- Extract info from the image and output as json
    + delivery-receipt-grab.jpg
    + receipt-thai.jpg
    + receipt-vn.webp

- Extract info from the image, output as json in English.
- Extract info from the image, output as xml in English without original words.
- Reformat last output as json.


## 2. Research
- Fun research 
- Deep research 

### Prompt
- Do fun search of above dishes and ranking by nutrition and calories, output as table
- Do fun search of above food and recommend the heahtiest food for young kids

- Reformat content, output as table, include name & description


## 3. Delivery helper to identify missing items 

### Prompt
- Check items based on receipt, if there's missing one?
+ bread-payment.jpg
+ bread-items.jpg

- Check the images if there's missing item based on receipt
- Describe the image
- Here's the receipt for first image, what's the potential missing item?

- Draft a complain email to the restaurant based on all the information collected above.


>>> Example 1
Check items based on receipt, if there's missing one?

+ bread-payment.jpg
+ bread-items.jpg
>>>
After reviewing your receipt against the items you received, there are a few discrepancies. Here is a summary of the findings:

Summary of Discrepancies:

Missing Item: The "Walnut & Cranberry Soft Loaf" listed on your receipt appears to be missing. Instead, you received a bagel-like pastry which was not on the receipt. Typically, a "Walnut & Cranberry Loaf" is a type of bread, often in a traditional loaf shape.
Incorrect Quantity: The receipt shows one "Chicken Sausage Bun," but you received two.
Item Breakdown:

Item on Receipt	Quantity on Receipt	Item in Image	Quantity in Image	Status
Walnut & Cranberry Soft Loaf	1	Bagel-like pastry	1	Missing/Incorrect Item
Chicken Sausage Bun	1	Sausage Buns	2	Incorrect Quantity
Cheese Doughnut	1	Round Pastries	2	Potentially Correct*
Crispy Cream Cheese Bun	1			Potentially Correct*
*It is likely that the two round pastries you received are the "Cheese Doughnut" and the "Crispy Cream Cheese Bun."

An invoice discrepancy occurs when there is a mismatch between what was ordered and what was delivered. This can include incorrect quantities or wrong items.

It is recommended to contact the vendor to report the missing and incorrect items. Many delivery services have a feature in their app or website to report these issues for a potential refund or credit.





