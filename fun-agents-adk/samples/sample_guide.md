# Demos for fun agents
## 1. Extract information from images in different languages: Thai, Vietnamese, Indonesian, etc  
- Translation
- Extracting
- Output with structure data: Json 
1 x Food item (Vietnamese) , 1 x driving license (Thai), 1 x bank invoice/statement (Bahasa)

### Prompt

- Extract info from the image and output as json

>>>
    + delivery-receipt-grab.jpg
    + receipt-thai.jpg
    + receipt-vn.webp
    + driver-example-th.jpg
    + hk_ID_card.jpg

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

>>>

    + bread-payment.jpg
    + bread-items.jpg


- Check the images if there's missing item based on receipt
- Describe the image
- Here's the receipt for first image, what's the potential missing item?

- Draft a complain email to the restaurant based on all the information collected above.


## 4. Gemini spatial understanding

### Prompt 
- Detecting items
- Detecting 2D stuff

../spatial-understanding


## 5. Gemini Live APIs

AI Studio or ADK 

- Bidirectional communication: different language: all major ASEAN languages vs English
    + Vietnam 
    + Singapore English
- Grounding with Google Search
- Identify food + Google Search as tool to provide real time information
- Identify objects: pens, anything







