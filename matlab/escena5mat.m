% ============================================================
%  ARCHIVO: escena5mat.m
%  Escena 5 – Objetos con TEXTURAS (checker / brick / voronoi)
%  Mismos colores base que escena 4.
%  Las texturas fragmentan la región → más cierre morfológico
%  y umbral de saturación más bajo para no perder zonas blancas
%  de checker/brick.
% ============================================================
clear; clc; close all;

dir_datos  = fullfile('datos',   'escena5');
dir_salida = fullfile('salidas', 'escena5');
if ~exist(dir_salida,'dir'), mkdir(dir_salida); end

secs = {'escena5_1','escena5_2','escena5_3'};

for e = 1:numel(secs)
    nom  = secs{e};
    din  = fullfile(dir_datos,  nom);
    dout = fullfile(dir_salida, [nom '_salida']);
    if ~exist(dout,'dir'), mkdir(dout); end

    arch = dir(fullfile(din,'*.png'));
    if isempty(arch), fprintf('Sin imágenes en %s\n', din); continue; end

    vid = VideoWriter(fullfile(dir_salida, [nom '_salida.mp4']), 'MPEG-4');
    vid.FrameRate = 1; open(vid);

    for k = 1:numel(arch)
        img = imread(fullfile(din, arch(k).name));
        hsv = rgb2hsv(img);
        H   = hsv(:,:,1);
        S   = hsv(:,:,2);

        % Umbral de saturación más bajo: las texturas mezclan zonas de color
        % con blanco/negro, reduciendo la saturación media de cada parche.
        bw_c = S > 0.18;

        % Cierre morfológico con disco mayor para unir fragmentos de textura
        bw_c = imopen(bw_c,  strel('disk', 2));
        bw_c = imclose(bw_c, strel('disk', 18));  % más grande que en escena 4
        bw_c = imfill(bw_c,  'holes');
        bw_c = bwareaopen(bw_c, 400);

        [lbl, ~] = bwlabel(bw_c);
        st = regionprops(lbl, 'Centroid','BoundingBox','Area');
        io = img; nd = 0;

        for i = 1:numel(st)
            A = st(i).Area; if A < 400, continue; end
            nd = nd + 1;
            cx = st(i).Centroid(1);  cy = st(i).Centroid(2);
            bb = st(i).BoundingBox;

            % Color dominante: umbral de saturación más bajo que escena 4
            mask  = lbl == i;
            h_reg = H(mask);  s_reg = S(mask);
            h_sat = h_reg(s_reg > 0.18);
            if isempty(h_sat), h_sat = h_reg; end
            hm = median(h_sat);

            if hm < 0.04 || hm > 0.95
                nom_c = 'Rojo';     c = 'red';
            elseif hm < 0.10
                nom_c = 'Naranja';  c = [255 140 0];
            elseif hm < 0.22
                nom_c = 'Amarillo'; c = [200 180 0];
            elseif hm < 0.52
                nom_c = 'Verde';    c = 'green';
            else
                nom_c = 'Azul';     c = 'blue';
            end

            io = insertShape(io,  'Rectangle', bb,   'Color',c, 'LineWidth',2);
            io = insertMarker(io, [cx cy],      '+',  'Color',c, 'Size',15);
            io = insertText(io,   [cx-30 cy-22], nom_c, 'FontSize',11, ...
                'TextColor',c, 'BoxColor','white', 'BoxOpacity',0.65);
        end

        io = insertText(io, [5 5], sprintf('F%d/%d | Det:%d', k, numel(arch), nd), ...
            'FontSize',12,'TextColor','black','BoxColor','white','BoxOpacity',0.8);
        imwrite(io, fullfile(dout, arch(k).name));
        writeVideo(vid, io);
    end
    close(vid);
    fprintf(' %s_salida generada\n', nom);
end
fprintf('=== Escena 5 completa ===\n');