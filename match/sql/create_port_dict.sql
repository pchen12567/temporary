CREATE TABLE ports.port_dict(
id serial PRIMARY KEY,
port_code VARCHAR(255) DEFAULT NULL,
port_name VARCHAR(255) DEFAULT NULL,
source int DEFAULT 0,
flag int DEFAULT 0,
create_time timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP,
update_time timestamp(0) DEFAULT NULL
);

ALTER TABLE "ports"."port_dict"
  OWNER TO "dbuser";

insert into "ports"."port_dict" (port_code,port_name)
select unctad,name from ports.port;
INSERT INTO  "ports"."port_dict"("port_code", "port_name", "source", "flag") VALUES ('SINGPEBGA', 'Singapore', 3, 1);
INSERT INTO  "ports"."port_dict"("port_code", "port_name", "source", "flag") VALUES ('SGEBGA', 'Singapore', 3, 1);
INSERT INTO  "ports"."port_dict"("port_code", "port_name", "source", "flag") VALUES ('CHINA', 'Shanghai', 3, 1);
INSERT INTO  "ports"."port_dict"("port_code", "port_name", "source", "flag") VALUES ('CNHKG', 'Hong Kong', 3, 1);