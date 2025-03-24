@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        youtube_url = data.get('url')
        category = data.get('category')
        ticker_symbol = data.get('ticker_symbol')

        if not youtube_url or not category:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: url and category"
            }), 400

        if category == 'Finance' and not ticker_symbol:
            return jsonify({
                "status": "error",
                "message": "Ticker symbol is required for Finance category"
            }), 400

        if not processor.assemblyai_api_key:
            return jsonify({
                "status": "error",
                "message": "AssemblyAI API key not configured"
            }), 500

        # Process the video
        result = processor.process_url(youtube_url, category, ticker_symbol)
        
        if result["status"] == "error":
            return jsonify(result), 500
        elif result["status"] == "cancelled":
            return jsonify(result), 200
            
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500 