# Api-to-Kafka

Simple utility to scrape an API and emit the timestamped data to a Kafka broker.

## Example

~~~bash
docker run --rm docker.pkg.github.com/homelycode/api-to-kafka/a2k:latest \
	--icmp -b redpanda:9092 -k wibeee \
	-u http://192.168.1.XXX/services/user/values.xml\?id\=Home xml \
	-x '$now' \
	-x "./variable[./id = 'vrms1']/value/text()" \
    -x "./variable[./id = 'irms1']/value/text()" \
    -x "./variable[./id = 'pap1']/value/text()" \       
    -x "./variable[./id = 'pac1']/value/text()" \            
    -x "./variable[./id = 'preac1']/value/text()" \                 
    -x "./variable[./id = 'freq1']/value/text()" \                   
    -x "./variable[./id = 'fpot1']/value/text()" \                        
    -x "./variable[./id = 'eac1']/value/text()" \                           
    -x "./variable[./id = 'ereactl1']/value/text()" \
    -x "./variable[./id = 'ereactc1']/value/text()"                                    
~~~

This can then for example be used to create a view via  https://materialize.com/docs/sql/create-source/

~~~sql
USE iot;

CREATE SOURCE s_csv_wibeee (ts,vrms1,irms1,pap1,pac1,preac1,freq1,fpot1,eac1,ereactl1,ereactc1)
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'wibeee'
FORMAT CSV WITH 11 COLUMNS;

CREATE MATERIALIZED VIEW v_wibeee AS 
	SELECT ts::timestamp, vrms1::float, irms1::float, pap1::float, pac1::float, preac1::float,freq1::float, fpot1::float, eac1::float, ereactl1::float, ereactc1::float
	FROM s_csv_wibeee;
~~~